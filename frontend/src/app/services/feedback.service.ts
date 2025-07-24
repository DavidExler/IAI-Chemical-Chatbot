import { Injectable } from "@angular/core";
import { environment } from "../../environments/environment";
import { HttpClient } from "@angular/common/http";
import { catchError, map, Observable } from "rxjs";
import { Feedback } from "../models/feedback";

@Injectable({
    providedIn: "root",
})
export class FeedbackService {
    backend_url = environment.backend_base_url;

    constructor(private http: HttpClient) {}

    sendFeedback(messageId: string, feedback: Feedback): Observable<boolean> {
        return this.http
            .post(`${this.backend_url}/feedback/${messageId}`, feedback)
            .pipe(
                map((_) => true),
                catchError((_) => [false]),
            );
    }
}
