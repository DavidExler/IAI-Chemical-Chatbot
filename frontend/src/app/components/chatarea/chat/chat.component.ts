import {
    AfterContentInit,
    ChangeDetectorRef,
    Component,
    effect,
    ElementRef,
    input,
    model,
    OnInit,
    ViewChild,
} from "@angular/core";
import { Conversation, Message } from "../../../models/conversation";
import { ConversationService } from "../../../services/conversation.service";
import { AsyncPipe, JsonPipe, NgTemplateOutlet } from "@angular/common";
import {
    MatCard,
    MatCardActions,
    MatCardContent,
} from "@angular/material/card";
import { MatButton, MatIconButton } from "@angular/material/button";
import { MatIcon } from "@angular/material/icon";
import { MarkdownComponent } from "ngx-markdown";
import { MatDialog } from "@angular/material/dialog";
import { ChatMessageFeedbackComponent } from "./chat-message-feedback/chat-message-feedback.component";
import { FeedbackService } from "../../../services/feedback.service";
import { filter, switchMap } from "rxjs";
import { StreamMessage } from "../../../models/langserve";
import { MatTab, MatTabGroup } from "@angular/material/tabs";
import {
    MatStep,
    MatStepLabel,
    MatStepper,
    MatStepperNext,
    MatStepperPrevious,
} from "@angular/material/stepper";
import { MatCheckbox } from "@angular/material/checkbox";

@Component({
    selector: "app-chat",
    standalone: true,
    imports: [
        AsyncPipe,
        JsonPipe,
        MatCard,
        MatCardContent,
        MatCardActions,
        MatIconButton,
        MatIcon,
        MarkdownComponent,
        MatTabGroup,
        MatTab,
        NgTemplateOutlet,
        MatStepper,
        MatStep,
        MatStepLabel,
        MatStepperNext,
        MatStepperPrevious,
        MatButton,
        MatCheckbox,
    ],
    templateUrl: "./chat.component.html",
    styleUrl: "./chat.component.scss",
})
export class ChatComponent implements OnInit, AfterContentInit {
    conversation = model<Conversation | null>();
    reloadMessages = model<boolean>();
    isGenerating = input<boolean>();
    newPrompt = input<string | null>();
    newResponse = input<StreamMessage | null>();
    messages!: Message[];

    private userScrolled: boolean = false;

    @ViewChild("messages_element")
    private messagesElement!: ElementRef<HTMLDivElement>;

    constructor(
        private conversationService: ConversationService,
        private feedbackService: FeedbackService,
        private changeDetector: ChangeDetectorRef,
        private feedbackDialog: MatDialog,
    ) {
        effect(() => {
            this.loadMessages();
        });
        effect(
            () => {
                if (this.reloadMessages()) {
                    this.loadMessages();
                    this.reloadMessages.set(false);
                }
            },
            {
                allowSignalWrites: true,
            },
        );
    }

    ngOnInit() {
        this.loadMessages();
    }

    ngAfterContentInit() {
        this.scrollToBottom();
    }

    copyToClipboard(content: string, icon: MatIcon) {
        navigator.clipboard
            .writeText(content)
            .then(() => this.checkIcon(icon))
            .catch(() => this.checkIcon(icon, 5000, false));
    }

    checkIcon(icon: MatIcon, timeout: number = 3000, success: boolean = true) {
        let initialIcon = icon.fontIcon;
        let initialColor = icon.color;

        icon.fontIcon = success ? "check" : "close";
        icon.color = success ? "primary" : "warn";
        this.changeDetector.detectChanges();

        setTimeout(() => {
            icon.fontIcon = initialIcon;
            icon.color = initialColor;
            this.changeDetector.detectChanges();
        }, timeout);
    }

    private loadMessages() {
        let conversation_uuid = this.conversation()?.uuid;
        if (!conversation_uuid) return;
        this.conversationService
            .getMessages(conversation_uuid)
            .subscribe((messages) => {
                this.messages = messages;
                this.changeDetector.detectChanges();
            });
    }

    private scrollToBottom() {
        console.debug("scrolling to bottom");
        const scrollToBottom = () => {
            const elem = this.messagesElement?.nativeElement;
            if (!elem) return;
            elem.onload = () => (elem.scrollTop = elem.scrollHeight);
            elem.onscroll = () => {
                this.userScrolled =
                    elem.scrollTop + elem.clientHeight < elem.scrollHeight;
            };
            if (!this.userScrolled) elem.scrollTop = elem.scrollHeight;
        };
        setInterval(() => scrollToBottom(), 100);
    }

    openFeedbackDialog(messageId: string, type: "up" | "down") {
        let feedback = { type, feedback: "", expected_answer: "" };
        this.feedbackDialog
            .open(ChatMessageFeedbackComponent, {
                data: { feedback },
                width: "60vw",
            })
            .afterClosed()
            .pipe(
                filter((f) => f !== undefined),
                switchMap((f) =>
                    this.feedbackService.sendFeedback(messageId, f),
                ),
            )
            .subscribe((result) => {
                if (result) console.info("Feedback sent successfully");
                else console.error("Failed to send feedback");
            });
    }
}
