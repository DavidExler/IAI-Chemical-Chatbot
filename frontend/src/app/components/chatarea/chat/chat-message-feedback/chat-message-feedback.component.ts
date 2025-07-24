import { Component, inject, model } from "@angular/core";
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogClose,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle,
} from "@angular/material/dialog";
import { MatFormField, MatLabel } from "@angular/material/form-field";
import { FormsModule } from "@angular/forms";
import { Feedback } from "../../../../models/feedback";
import { MatInput } from "@angular/material/input";
import { MatButton } from "@angular/material/button";
import { JsonPipe } from "@angular/common";
import { CdkTextareaAutosize } from "@angular/cdk/text-field";

@Component({
    selector: "app-chat-message-feedback",
    standalone: true,
    imports: [
        MatDialogContent,
        MatFormField,
        FormsModule,
        MatDialogActions,
        MatDialogClose,
        MatDialogTitle,
        MatInput,
        MatButton,
        MatLabel,
        JsonPipe,
        CdkTextareaAutosize,
    ],
    templateUrl: "./chat-message-feedback.component.html",
})
export class ChatMessageFeedbackComponent {
    readonly dialogRef = inject(MatDialogRef<ChatMessageFeedbackComponent>);
    readonly data = inject<{ feedback: Feedback }>(MAT_DIALOG_DATA);
    readonly feedback = model(this.data.feedback);

    onNoClick(): void {
        this.dialogRef.close();
    }
}
