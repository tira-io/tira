CLI Commands
============

Adding a new subcommand
-----------------------
Currently, all TIRA CLI subcommands live within ``python-client/tira/tira_cli.py``. For this tutorial we will create a
new subcommand ``tira-cli repeat <number> --text <text>`` that is supposed to print the given text, ``<text>``,
``<number>`` times to the console and exit. We already implemented this functionality in the following function

.. code:: py

    def repeat_command(number: int, text: str, **kwargs) -> int:
        for _ in range(number):
            print(text)
        return 0

.. note:: We return 0 to indicate success. Any return code other than 0 should indicate failure and, if you like, you can
    use the return code to communicate different kinds of failures to the user.

.. attention:: The ``**kwargs`` parameter is important! For ease of use, we forward all command line arguments into the
    command. Try and see what happens if you remove the ``**kwargs`` or print them to console if you want to understand
    it better.

Now, we only need to register this command with TIRA and tell it the arguments we need. We do this by creating a new
method within ``python-client/tira/tira_run.py`` like this:

.. code:: py

    def setup_repeat_command(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("number", type=int, help="The number of times the chosen text should be printed")
        parser.add_argument("-t", "--text", required=False, default="Hi", type=str, help="The text that should be printed")

        # Register the repeat_command method as the "main"-method
        # This is important as it tells TIRA what command should be run.
        parser.set_defaults(executable=repeat_command)

.. note:: The naming scheme of using ``setup_{commandname}_command`` to register the command ``{commandname}_command``
    is "just" a guideline. But, for consistency, please adhere to it.

.. attention:: The argument names are important. To see why, try and remove ``"--text"`` such that the text-argument can
    only be invoked via ``-t``. Now, ``repeat_command`` won't have its ``text`` parameter set correctly if you supply
    the argument. You should use the `dest <https://docs.python.org/3/library/argparse.html#dest>`_ parameter of
    ``add_argument`` to specify the parameter-name the argument should be stored in when calling your command
    implementation. In this case, it should read:

    .. code:: py

        parser.add_argument("-t", required=False, default="Hi", dest="text", type=str, help="The text that should be printed")

The only thing left to do now is to call this setup function in TIRA's setup code and we are done! To do so, find the
following line of code within ``python-client/tira/tira_run.py``.

.. code:: py

    subparsers = parser.add_subparsers()

We use the lines below to register our subcommands. Register your subcommand where appropriate (e.g., in alphabetical
order). It should now look something like this:

.. code-block:: python
    :emphasize-lines: 3

    subparsers = parser.add_subparsers()
    setup_a_thing_command(subparsers.add_parser('a-thing', help="I do stuff"))
    setup_repeat_command(subparsers.add_parser('repeat', help="Repeat the provided text any number of times"))
    setup_something_else_command(subparsers.add_parser('something-else', help="I do other stuff"))

We are done! To test your brand new command, set the ``PYTHONPATH`` environment variable to the path to
``python-client``. This overrides where the ``tira-cli`` command is loaded from. For example, if you have cloned the
repository to ``/home/me/repos/tira``, you can set the PYTHONPATH by running
``export PYTHONPATH=/home/me/repos/tira/python-client`` from the terminal. Now you can call the help page for your
command and should get the following output:

.. code:: sh

    $ tira-cli repeat --help

    usage: tira-cli repeat [-h] [-t,--text T,__TEXT] number

    positional arguments:
    number              The number of times the chosen text should be printed

    options:
    -h, --help          show this help message and exit
    -t,--text T,__TEXT  The text that should be printed

Make sure that it works by also trying out

.. code:: sh
    
    $ tira-cli repeat 3
    $ tira-cli repeat 3 --text "I like TIRA"
    $ tira-cli repeat 5 -t "I like TIRA"
    $ tira-cli repeat
    $ tira-cli repeat not-a-number

What would you expect should happen? Does it work?

.. important:: Please, do not forget to add documentation of your new subcommand to the
    :ref:`TIRA CLI documentation <TIRACLIPage>`.

Adding Logging to our Subcommand
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For consistency, some arguments should look and feel the same across subcommands. A good example may be the logging
arguments (``--quiet`` and ``--verbose``). These argument definitions should be defined in separate functions (e.g.,
``setup_logging_args`` for logging) such that they can be reused. In effect this means that adding such functionality to
our subcommand is as simple as calling these setup-functions. Concretely, for logging, this means that we can configure
logging for our Subcommand simply by modifying the ``setup_repeat_command`` method such that it reads

.. code-block:: py
    :emphasize-lines: 2

    def setup_repeat_command(parser: argparse.ArgumentParser) -> None:
        setup_logging_args(parser)
        parser.add_argument("number", type=int, help="The number of times the chosen text should be printed")
        parser.add_argument("-t", "--text", required=False, default="Hi", type=str, help="The text that should be printed")

        # Register the repeat_command method as the "main"-method
        # This is important as it tells TIRA what command should be run.
        parser.set_defaults(executable=repeat_command)

Test it by adding logs to your subcommand (``logging.debug``, ``logging.info``, ``logging.warning``, ``logging.error``,
``logging.critical``) and append ``-v``, ``-q`` and ``-vv`` to your command. What do you expect and what happens? Consider
that the default log-level is ``INFO``.

.. note:: Keep in mind that logging can be disabled by the user, redirected to a file or formatted arbitrarily (e.g.,
    JSON logs for deployment but simple text logs for development). This means that anything that semantically should
    or must be printed to the console should not be logged but printed instead.


Typing Arguments (A more complex example)
-----------------------------------------
Not all arguments are primitives like ``str`` or ``int``. While we could encode all arguments this way and let our code
check if the argument follows the correct format, this does not follow the philosphy behind Python's ``argparse`` API
and should be avoided (unless it is more readable). To illustrate this, we want to create the CLI for the following
function:

.. code:: py

    def writestuff_command(input: TextIO, output: TextIO, approach: Approach, **kwargs) -> None:
        """
        Creates a new file at the specified output path and writes the following lines to it:
        <first line of the input file>\\n
        <approach.taskid>\\n
        <approach.userid>\\n
        <approach.name>\\n
        """
        output.write(f"{input.readline()}\n{approach.taskid}\n{approach.userid}\n{approach.name}\n")


Here, ``Approach`` is a `named tuple <https://docs.python.org/3/library/typing.html#typing.NamedTuple>`_:

.. code:: py

    class Approach(NamedTuple):
        taskid: str
        userid: str
        name: str

which the user should provide on the CLI as ``--approach <task-id>/<user-id>/<approach-name>``. To enforce this
behavior, we generally do the same as for ``repeat_command`` but we use the ``type`` argument to convert the arguments
from strings and enforce constraints (e.g., that the input-path must exist). This may look like this:

.. code:: py

    # Please don't place me with the setup_..._command methods but somewhere else to keep tira_cli.py clutter free :)
    def approach_from_str(text: str) -> Approach:
        split = text.split('/')
        if len(split) != 3:
            raise argparse.ArgumentTypeError("Approaches MUST be encoded as '<task-id>/<user-id>/<approach-name>'")
        return Approach(taskid=split[0], userid=split[1], name=split[2])

    def setup_writestuff_command(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("input", type=argparse.FileType('r'), help="...")
        parser.add_argument("-o", type=argparse.FileType('w'), dest="output", required=True, help="...")
        parser.add_argument("--approach", type=approach_from_str, required=True, help="...")
        parser.set_defaults(executable=writestuff_command)

Don't forget to register the subcommand and check with ``tira-cli writestuff --help`` that it works. Now play around
with different arguments. For example:

.. code:: sh
    
    $ tira-cli writestuff <non-existent-file> -o <file> --approach task/user/name
    $ tira-cli writestuff <existing-file> -o <file> --approach task/user/name
    $ tira-cli writestuff <existing-file> -o <file> --approach task/user

Does it do what you expect?

.. hint:: ``argparse.FileType`` has the neat feature that it can also pass ``stdin`` and ``stdout`` to your command if
    you set the parameter value to ``-`` (you may already know this notation, e.g., from ``wget``), like so:

    .. code:: sh
        
        $ echo "Hello World" | tira-cli writestuff - -o- --approach task/user/name


Implementation Details and Hints
--------------------------------
- For argument parsing, we use Python's `argparse <https://docs.python.org/3/library/argparse.html>`_ library. If you
  want to find more information on how to properly configure your command line arguments, their documentation is a good
  start.
- Please keep in mind that some arguments are already in use by TIRA and could cause problems if you are not careful.
  These are ``command`` and ``executable``. If you want to use such a name for your argument (e.g., ``--command``), you
  can do so but you have to set the `dest <https://docs.python.org/3/library/argparse.html#dest>`_ argument to something
  other than the protected names.