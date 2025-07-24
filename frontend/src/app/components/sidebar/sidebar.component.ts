import {
    ChangeDetectorRef,
    Component,
    effect,
    ElementRef,
    model,
    OnInit,
    ViewChild,
} from "@angular/core";
import { MatButton, MatIconButton } from "@angular/material/button";
import { MatIcon } from "@angular/material/icon";
import { MatDivider } from "@angular/material/divider";
import { ConversationService } from "../../services/conversation.service";
import { Observable } from "rxjs";
import { Conversation } from "../../models/conversation";
import { AsyncPipe, JsonPipe } from "@angular/common";
import { MatProgressSpinner } from "@angular/material/progress-spinner";

@Component({
    selector: "app-sidebar",
    standalone: true,
    imports: [
        MatButton,
        MatIcon,
        MatDivider,
        MatIconButton,
        AsyncPipe,
        MatProgressSpinner,
        JsonPipe,
    ],
    templateUrl: "./sidebar.component.html",
    styleUrl: "./sidebar.component.scss",
})
export class SidebarComponent implements OnInit {
    conversation = model<Conversation | null>();

    @ViewChild("pastConversations")
    pastConversations!: ElementRef<HTMLDivElement>;

    updatedConversations: Conversation[] = [];
    conversations!: Observable<Conversation[]>;

    constructor(
        private conversationService: ConversationService,
        private changeDetector: ChangeDetectorRef,
    ) {
        effect(() => {
            let conversation = this.conversation();
            if (conversation) {
                this.updateConversation(conversation);
            }
            this.changeDetector.detectChanges();
        });
    }

    ngOnInit() {
        this.loadConversations();
    }

    createConversation() {
        this.conversationService
            .createConversation()
            .subscribe((conversation) => {
                this.loadConversations();
                this.selectConversation(conversation);
                console.info("Created conversation", conversation);
            });
    }

    selectConversation(conversation: Conversation | null) {
        if (conversation === this.conversation()) {
            console.debug("Conversation already selected");
            return;
        }
        this.conversation.set(conversation);
    }

    deleteConversation(conversation: Conversation) {
        this.conversationService
            .deleteConversation(conversation)
            .subscribe((success) => {
                if (success) {
                    this.loadConversations();
                    if (this.conversation()?.uuid === conversation.uuid) {
                        this.selectConversation(null);
                    }
                } else {
                    console.error("Failed to delete conversation");
                }
            });
    }

    getUpdatedConversation(c: Conversation) {
        return this.updatedConversations.find((uc) => uc.uuid === c.uuid) ?? c;
    }

    private loadConversations() {
        this.conversations = this.conversationService.getConversations();
        this.changeDetector.detectChanges();
    }

    private updateConversation(conversation: Conversation) {
        let index = this.updatedConversations.findIndex(
            (c) => c.uuid === conversation.uuid,
        );
        if (index === -1) {
            this.updatedConversations.push(conversation);
        } else {
            console.log("Updating conversation", conversation);
            this.updatedConversations[index] = conversation;
        }
    }
}
