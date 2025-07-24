import { Component, model, signal } from "@angular/core";
import { Conversation } from "../../models/conversation";
import { FormsModule } from "@angular/forms";
import {
    MatExpansionPanel,
    MatExpansionPanelHeader,
    MatExpansionPanelTitle,
} from "@angular/material/expansion";
import { MatLabel } from "@angular/material/form-field";
import { MatRadioButton, MatRadioGroup } from "@angular/material/radio";
import { AsyncPipe, JsonPipe } from "@angular/common";
import { SettingsComponent } from "./settings/settings.component";
import {
    MatList,
    MatListItem,
    MatListOption,
    MatSelectionList,
} from "@angular/material/list";
import { MatIcon } from "@angular/material/icon";
import { MatIconButton } from "@angular/material/button";
import { MatCard, MatCardContent } from "@angular/material/card";
import { ChatPromptComponent } from "./chat-prompt/chat-prompt.component";
import { ChatComponent } from "./chat/chat.component";
import { LangserveService } from "../../services/langserve.service";
import { finalize, Subscription } from "rxjs";
import { LangserveMessageEvent, StreamMessage } from "../../models/langserve";

@Component({
    selector: "app-chatarea",
    standalone: true,
    imports: [
        MatExpansionPanel,
        MatExpansionPanelHeader,
        MatExpansionPanelTitle,
        MatLabel,
        MatRadioGroup,
        MatRadioButton,
        FormsModule,
        AsyncPipe,
        SettingsComponent,
        MatList,
        JsonPipe,
        MatSelectionList,
        MatListOption,
        MatIcon,
        MatIconButton,
        MatCard,
        MatCardContent,
        MatListItem,
        ChatPromptComponent,
        ChatComponent,
    ],
    templateUrl: "./chat-area.component.html",
    styleUrl: "./chat-area.component.scss",
})
export class ChatAreaComponent {
    conversation = model<Conversation | null>();
    reloadMessages = model<boolean>(false);
    reloadConversation = model<boolean>(false);
    isGenerating = signal<boolean>(false);
    newPrompt = signal<string | null>(null);
    newResponse = signal<StreamMessage | null>(null);
    private streamSubscription?: Subscription;

    constructor(private langserveService: LangserveService) {}

    prompt(message: string | null) {
        if (message === null) {
            this.cancelGeneration();
            return;
        }

        if (message.length === 0) {
            console.warn("Empty message");
            return;
        }

        let conversation = this.conversation();
        if (!conversation) {
            console.error("No conversation");
            return;
        }

        if (this.isGenerating()) {
            console.warn("Already generating");
            return;
        }

        this.isGenerating.set(true);
        this.newPrompt.set(message);
        this.streamSubscription = this.langserveService
            .promptConversation(conversation, message)
            .pipe(
                finalize(() => {
                    this.newPrompt.set(null);
                    this.newResponse.set(null);
                    this.isGenerating.set(false);
                    this.reloadMessages.set(true);
                    this.reloadConversation.update((p) => !p);
                }),
            )
            .subscribe((event: LangserveMessageEvent) => {
                if (event.event !== "on_chain_stream") return;
                let chunk = event.data.chunk;
                console.debug("Received chunk", chunk);
                this.newResponse.update((prev) => {
                    if (prev === null) prev = { content: "" };
                    let newContent;
                    let newSteps = [];
                    if (typeof chunk === "string") {
                        newContent = chunk;
                    } else if ("content" in chunk) {
                        newContent = chunk.content;
                    } else if ("output" in chunk) {
                        newContent = chunk.output;
                    } else {
                        newContent =
                            chunk.messages
                                .filter((m) => m.type === "ai")
                                .map((m) => m.content)
                                .join("\n") + "\n";
                    }
                    if (typeof chunk !== "string" && "steps" in chunk) {
                        newSteps.push(...(chunk.steps ?? []));
                    }
                    return {
                        content: prev.content + newContent,
                        steps: prev.steps
                            ? [...prev.steps, ...newSteps]
                            : newSteps,
                    };
                });
            });
    }

    cancelGeneration() {
        console.debug("Cancel generation");
        this.streamSubscription?.unsubscribe();
    }
}
