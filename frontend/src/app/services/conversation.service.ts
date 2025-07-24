import { Injectable } from "@angular/core";
import { environment } from "../../environments/environment";
import { HttpClient } from "@angular/common/http";
import { catchError, map, Observable } from "rxjs";
import {
    Conversation,
    ConversationSettings,
    Document,
    Message,
} from "../models/conversation";

@Injectable({
    providedIn: "root",
})
export class ConversationService {
    backend_url = environment.backend_base_url;

    constructor(private http: HttpClient) {}

    public getConversations(): Observable<Conversation[]> {
        console.debug("Getting conversations");
        return this.http.get<Conversation[]>(
            `${this.backend_url}/conversations`,
        );
    }

    public getConversation(uuid: string): Observable<Conversation> {
        console.debug("Getting conversation", uuid);
        return this.http.get<Conversation>(
            `${this.backend_url}/conversations/${uuid}`,
        );
    }

    public getDocuments(conversation_uuid: string) {
        console.debug("Getting documents for conversation", conversation_uuid);
        return this.http.get<Document[]>(
            `${this.backend_url}/conversations/${conversation_uuid}/documents`,
        );
    }

    public getMessages(conversation_uuid: string) {
        console.debug("Getting messages for conversation", conversation_uuid);
        return this.http.get<Message[]>(
            `${this.backend_url}/conversations/${conversation_uuid}/messages`,
        );
    }

    public createConversation() {
        console.debug("Creating conversation");
        return this.http.post<Conversation>(
            `${this.backend_url}/conversations`,
            {},
        );
    }

    public updateSettings(uuid: string, settings: ConversationSettings) {
        console.debug("Updating settings for conversation", uuid, settings);
        return this.http.put<Conversation>(
            `${this.backend_url}/conversations/${uuid}/settings`,
            settings,
        );
    }

    public uploadDocuments(uuid: string, documents: File[]) {
        console.debug("Uploading documents for conversation", uuid, documents);
        let formData = new FormData();
        documents.forEach((document) => {
            formData.append("files", document);
        });

        return this.http.post<Conversation>(
            `${this.backend_url}/conversations/${uuid}/documents`,
            formData,
            {
                reportProgress: true,
                observe: "events",
            },
        );
    }

    public deleteConversation(conversation: Conversation) {
        console.debug("Deleting conversation", conversation);
        return this.http
            .delete(`${this.backend_url}/conversations/${conversation.uuid}`)
            .pipe(
                map(() => true),
                catchError(() => [false]),
            );
    }

    public deleteDocument(conversation_uuid: string, document_uuid: string) {
        console.debug("Deleting document", document_uuid);
        return this.http
            .delete(
                `${this.backend_url}/conversations/${conversation_uuid}/documents/${document_uuid}`,
            )
            .pipe(
                map(() => true),
                catchError(() => [false]),
            );
    }
}
