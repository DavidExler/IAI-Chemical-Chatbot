import { Component, input, output, signal, ViewChild } from "@angular/core";
import { Conversation } from "../../../../models/conversation";
import { MatIcon } from "@angular/material/icon";
import { MatButton, MatIconButton } from "@angular/material/button";
import { MatList, MatListItem } from "@angular/material/list";
import { MatProgressBar } from "@angular/material/progress-bar";
import { ConversationService } from "../../../../services/conversation.service";
import { HttpEventType } from "@angular/common/http";
import { DecimalPipe } from "@angular/common";
import { MatProgressSpinner } from "@angular/material/progress-spinner";
import { MatError, MatLabel } from "@angular/material/form-field";
import { Subscription } from "rxjs";

@Component({
    selector: "app-file-upload",
    standalone: true,
    imports: [
        MatIcon,
        MatIconButton,
        MatList,
        MatListItem,
        MatProgressBar,
        DecimalPipe,
        MatProgressSpinner,
        MatLabel,
        MatError,
        MatButton,
    ],
    templateUrl: "./file-upload.component.html",
    styleUrl: "./file-upload.component.scss",
})
export class FileUploadComponent {
    conversation = input<Conversation | null>();
    onFileUploaded = output<FileList>();

    @ViewChild("fileUpload")
    fileUploader!: HTMLInputElement;

    progress = signal<number | null>(null);
    error?: string | null;
    private uploadSubscription?: Subscription;

    constructor(private conversationService: ConversationService) {}

    onFileSelected($event: Event) {
        let files = ($event.target as HTMLInputElement).files;
        if (!files || files.length == 0) return;

        this.uploadFiles(files);
    }

    cancelUpload() {
        if (this.uploadSubscription) {
            this.uploadSubscription.unsubscribe();
            this.uploadSubscription = undefined;
            this.error = null;
            this.progress.set(null);
        }
    }

    private uploadFiles(files: FileList) {
        this.error = null;

        let conversation_uuid = this.conversation()?.uuid;
        if (!conversation_uuid) {
            console.error("No conversation selected");
            return;
        }
        this.uploadSubscription = this.conversationService
            .uploadDocuments(conversation_uuid, Array.from(files))
            .subscribe({
                next: (event) => {
                    if (event.type == HttpEventType.UploadProgress) {
                        console.log("Upload progress", event);
                        this.progress.set(
                            event.loaded / Math.max(1, event.total ?? 1),
                        );
                    } else if (event.type == HttpEventType.Response) {
                        console.log("Upload complete");
                        this.progress.set(null);
                        this.onFileUploaded.emit(files);
                    }
                },
                error: (error) => {
                    console.error("Upload failed", error);
                    this.error = error.error.detail;
                    this.progress.set(null);
                },
            });
    }
}
