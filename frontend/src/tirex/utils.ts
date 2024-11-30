export interface Topic {
    qid: string;
    dataset_id: string;
    default_text: string;
    client_side_identifier: string | undefined;
    description: string | undefined;
    narrative: string | undefined;
}

export interface RunDetails {
    tira_run: string;
    dataset: string;
    team: string;
    run: string;
    client_side_identifier: string | undefined;
    system_link: string | undefined;
}

export function uniqueElements(elements: any[], key: string) {
    return [...new Set(elements.map(i => i[key]))]
}