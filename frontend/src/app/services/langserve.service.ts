import { Injectable } from "@angular/core";
import { Conversation } from "../models/conversation";
import { environment } from "../../environments/environment";
import { SseClient } from "ngx-sse-client";
import { catchError, filter, map, Observable, takeWhile } from "rxjs";
import { LangserveMessageEvent } from "../models/langserve";

@Injectable({
    providedIn: "root",
})
export class LangserveService {
    backend_url = environment.backend_base_url;

    constructor(private sseClient: SseClient) {}

    promptConversation(
        conversation: Conversation,
        input: string,
    ): Observable<LangserveMessageEvent> {
        const topic = `${this.backend_url}/chains/${conversation.chain}/stream_events`;

        return this.sseClient
            .stream(
                topic,
                {},
                {
                    body: {
                        input: { input },
                        config: {
                            configurable: {
                                conversation_id: conversation.uuid,
                                document_ids: conversation.documents.join(","),
                                tool_names: conversation.tools,
                                prompt: conversation.prompt,
                            },
                        },
                        include_names: [
                            "ChatOpenAI",
                            "/chains/rag",
                            "/chains/agent",
                            "/chains/code",
                            ...conversation.tools,
                        ],
                        version: "v1",
                    },
                },
                "POST",
            )
            .pipe(
                map((event) => {
                    if (event instanceof MessageEvent) {
                        return event;
                    } else if (event instanceof ErrorEvent) {
                        throw new Error(JSON.stringify(event));
                    } else {
                        console.warn("Unknown event type", event);
                        return null;
                    }
                }),
                filter((event) => event !== null),
                map((event) => JSON.parse(event.data)),
                takeWhile((event) => event.type !== "on_chain_end", true),
                catchError(() => []),
            );
    }
}
