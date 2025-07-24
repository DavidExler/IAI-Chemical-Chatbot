export interface LangserveMessageEvent {
    data: { chunk: string | Generation | StepGeneration };
    event: string;
    name: string;
    parent_ids: string[];
    run_id: string;
    tags: string[];
}

export interface StepGeneration {
    messages: Generation[];
    steps: MessageStep[];
}

export interface Generation {
    content: string;
    additional_kwargs: object;
    response_metadata: {
        logprobs?: {
            content: {
                token: string;
                logprob: number;
                top_logprobs: {
                    token: string;
                    logprob: number;
                }[];
            }[];
        };
        finish_reason?: string;
        model_name?: string;
    };
    type: "AIMessageChunk" | "HumanMessageChunk" | "ai" | "human";
    name?: string;
    id?: string;
}

export interface StreamMessage {
    content: string;
    steps?: MessageStep[];
}

export interface MessageStep {
    action: {
        tool: string;
        tool_input: string;
        log: string;
    };
    observation: string;
}
