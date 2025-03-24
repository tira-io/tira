export interface Topic {
    qid: string;
    dataset_id: string;
    default_text: string;
    client_side_identifier: string | undefined;
    description: string | undefined;
    narrative: string | undefined;
    runs: RunDetails[] | undefined;
    docs: Record<string, DiffIrDoc> | undefined;
}

export interface DiffIrDoc {
    snippet: any;
    weights: any;
}

export interface ScoredDoc {
    rank: number;
    score: number;
    doc_id: string;
}

export interface RunDetails {
    tira_run: string;
    dataset: string;
    team: string;
    run: string;
    client_side_identifier: string | undefined;
    title: string | undefined;
    system_link: string | undefined;
    ranking: Record<string, ScoredDoc[]> | undefined;
}

export function uniqueElements(elements: any[], key: string) {
    return [...new Set(elements.map(i => i[key]))]
}