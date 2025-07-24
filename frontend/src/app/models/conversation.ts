import { MessageStep } from "./langserve";

export interface Conversation {
    uuid: string;
    user_uuid: string;
    title: string;
    chain: string;
    prompt: string;
    tools: string[];
    documents: string[];
    created_at: string;
}

export interface ConversationSettings {
    selected_chain?: string;
    selected_prompt?: string;
    selected_tools?: string[];
    selected_documents?: string[];
}

export interface Document {
    uuid: string;
    conversation_uuid: string;
    title: string;
    type: string;
    filepath: string;
    created_at: string;
}

interface BaseMessage {
    id: string;
    name: string | null;
    example: boolean;
    content: string;
    response_metadata: JSON;
}

export interface HumanMessage extends BaseMessage {
    type: "human";
}

export interface AIMessage extends BaseMessage {
    type: "ai" | "AIMessageChunk";
    tool_calls: string[];
    invalid_tool_calls: string[];
    usage_metadata: JSON | null;
    additional_kwargs: {
        intermediate_steps?: MessageStep[];
    };
}

export type Message = AIMessage | HumanMessage;
