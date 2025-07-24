export interface Chain {
    name: string;
    path: string;
    description: string;
    supports_documents: boolean;
    tool_names: string[];
    prompt_names: string[];
}
