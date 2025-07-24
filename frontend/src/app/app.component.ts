import { ChangeDetectorRef, Component, effect, signal } from "@angular/core";
import { Conversation } from "./models/conversation";
import { LocalstorageService } from "./services/localstorage.service";
import { ConversationService } from "./services/conversation.service";
import { catchError } from "rxjs";

@Component({
    selector: "app-root",
    templateUrl: "./app.component.html",
    styleUrl: "./app.component.scss",
})
export class AppComponent {
    conversation = signal<Conversation | null>(null);

    constructor(
        private localstorageService: LocalstorageService,
        private conversationService: ConversationService,
        private changeDetector: ChangeDetectorRef,
    ) {
        let conversation = this.localstorageService.read("conversation");
        if (conversation?.uuid) {
            this.conversationService
                .getConversation(conversation.uuid)
                .pipe(catchError(() => [])) // We might want to create a new conversation if no conversation is selected currently
                .subscribe((c) => this.conversation.set(c));
        }
        effect(() =>
            this.localstorageService.write("conversation", this.conversation()),
        );
    }

    reloadConversation() {
        if (this.conversation()?.title === "New Conversation") {
            let conversation_uuid = this.conversation()?.uuid;
            if (conversation_uuid) {
                console.debug("Reloading conversation", conversation_uuid);
                this.conversationService
                    .getConversation(conversation_uuid)
                    .subscribe((c) => {
                        this.conversation.set(c);
                        this.changeDetector.detectChanges();
                    });
            }
        }
    }
}
