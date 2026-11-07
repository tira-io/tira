from django.test import TestCase
from utils_for_testing import dataset_1, set_up_tira_environment

import tira_app.model as modeldb
from tira_app import tira_model as model
from tira_app.data.HybridDatabase import HybridDatabase

PARTICIPANT = "example_participant"


class TestDeleteEvaluationRun(TestCase):
    """Tests for deleting evaluation runs (see HybridDatabase.delete_run/_delete_evaluation_run), which
    must remove the corresponding Evaluation rows (used to render the leaderboards) and must refuse the
    deletion if it would leave the evaluated submission without any remaining evaluation that still has
    Evaluation rows."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()

    def _submission_run(self, run_id: str) -> modeldb.Run:
        dataset = modeldb.Dataset.objects.get(dataset_id=dataset_1)
        return modeldb.Run.objects.create(run_id=run_id, input_dataset=dataset)

    def _evaluation_run(self, run_id: str, input_run: modeldb.Run) -> modeldb.Run:
        evaluator = modeldb.Evaluator.objects.get(evaluator_id="big-evaluator-for-everything")
        dataset = modeldb.Dataset.objects.get(dataset_id=dataset_1)
        eval_run = modeldb.Run.objects.create(
            run_id=run_id, input_run=input_run, input_dataset=dataset, evaluator=evaluator
        )
        modeldb.Evaluation.objects.create(measure_key="k-1", measure_value="1.0", run=eval_run)
        return eval_run

    def test_is_evaluation_run_is_true_for_properly_named_evaluation(self):
        submission = self._submission_run("sub-run-for-is-evaluation-test")
        eval_run = self._evaluation_run("ts-evaluates-sub-run-for-is-evaluation-test", submission)

        self.assertTrue(HybridDatabase._is_evaluation_run(eval_run))

    def test_is_evaluation_run_is_false_without_evaluates_in_run_id(self):
        submission = self._submission_run("sub-run-for-missing-evaluates-marker")
        eval_run = modeldb.Run.objects.create(
            run_id="some-run-id-without-the-marker",
            input_run=submission,
            input_dataset=modeldb.Dataset.objects.get(dataset_id=dataset_1),
            evaluator=modeldb.Evaluator.objects.get(evaluator_id="big-evaluator-for-everything"),
        )

        self.assertFalse(HybridDatabase._is_evaluation_run(eval_run))

    def test_is_evaluation_run_is_false_without_input_run(self):
        submission = self._submission_run("ts-evaluates-nothing")

        self.assertFalse(HybridDatabase._is_evaluation_run(submission))

    def test_deleting_one_of_multiple_evaluations_of_a_submission_succeeds(self):
        submission = self._submission_run("sub-run-with-two-evaluations")
        eval_run_1 = self._evaluation_run("ts-1-evaluates-sub-run-with-two-evaluations", submission)
        self._evaluation_run("ts-2-evaluates-sub-run-with-two-evaluations", submission)

        deleted = model.delete_run(dataset_1, PARTICIPANT, eval_run_1.run_id)

        self.assertTrue(deleted)
        eval_run_1.refresh_from_db()
        self.assertTrue(eval_run_1.deleted)
        self.assertFalse(modeldb.Evaluation.objects.filter(run=eval_run_1).exists())

    def test_deleting_the_last_remaining_evaluation_of_a_submission_is_refused(self):
        submission = self._submission_run("sub-run-with-single-evaluation")
        eval_run = self._evaluation_run("ts-evaluates-sub-run-with-single-evaluation", submission)

        deleted = model.delete_run(dataset_1, PARTICIPANT, eval_run.run_id)

        self.assertFalse(deleted)
        eval_run.refresh_from_db()
        self.assertFalse(eval_run.deleted)
        self.assertTrue(modeldb.Evaluation.objects.filter(run=eval_run).exists())
