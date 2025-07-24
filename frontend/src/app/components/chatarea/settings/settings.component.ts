import { ChangeDetectorRef, Component, effect, model } from "@angular/core";
import {
    Conversation,
    ConversationSettings,
    Document,
} from "../../../models/conversation";
import { Observable } from "rxjs";
import { Chain } from "../../../models/chain";
import { FormsModule } from "@angular/forms";
import { ChainsService } from "../../../services/chains.service";
import {
    MatExpansionPanel,
    MatExpansionPanelHeader,
    MatExpansionPanelTitle,
} from "@angular/material/expansion";
import { MatFormField, MatLabel } from "@angular/material/form-field";
import {
    MatRadioButton,
    MatRadioChange,
    MatRadioGroup,
} from "@angular/material/radio";
import { AsyncPipe, JsonPipe } from "@angular/common";
import { MatTooltip } from "@angular/material/tooltip";
import { ConversationService } from "../../../services/conversation.service";
import {
    MatOption,
    MatSelect,
    MatSelectChange,
} from "@angular/material/select";
import { FileUploadComponent } from "./file-upload/file-upload.component";
import { MatCardContent } from "@angular/material/card";
import { MatIcon } from "@angular/material/icon";
import { MatIconButton } from "@angular/material/button";
import {
    MatList,
    MatListItem,
    MatListOption,
    MatSelectionList,
} from "@angular/material/list";
import { MatProgressSpinner } from "@angular/material/progress-spinner";

@Component({
    selector: "app-settings",
    standalone: true,
    templateUrl: "./settings.component.html",
    imports: [
        MatExpansionPanel,
        MatExpansionPanelHeader,
        MatExpansionPanelTitle,
        MatLabel,
        MatRadioGroup,
        MatRadioButton,
        FormsModule,
        AsyncPipe,
        MatTooltip,
        MatSelect,
        MatOption,
        MatFormField,
        FileUploadComponent,
        MatCardContent,
        MatIcon,
        MatIconButton,
        MatList,
        MatListItem,
        MatSelectionList,
        MatListOption,
        JsonPipe,
        MatProgressSpinner,
    ],
    styleUrl: "./settings.component.scss",
})
export class SettingsComponent {
    conversation = model<Conversation | null>();

    public chains!: Observable<Chain[]>;
    public documents!: Observable<Document[]>;

    constructor(
        private chainService: ChainsService,
        private conversationService: ConversationService,
        private changeDetectorRef: ChangeDetectorRef,
    ) {
        this.chains = this.chainService.getAllChains();
        let conversation_uuid = this.conversation()?.uuid;
        console.log("Before Effect", conversation_uuid);
        effect(() => {
            let conversation_uuid = this.conversation()?.uuid;
            console.log("Conversation changed", conversation_uuid);
            if (!conversation_uuid) return;
            this.loadDocuments();
        });
    }

    changeChain($event: MatRadioChange) {
        let changedSettings = {
            selected_chain: $event.value as string,
        };
        this.updateConversationSettings(changedSettings);
    }

    changePrompt($event: MatRadioChange) {
        let changedSettings = {
            selected_prompt: $event.value as string,
        };
        this.updateConversationSettings(changedSettings);
    }

    changeTools($event: MatSelectChange) {
        let changedSettings = {
            selected_tools: $event.value as string[],
        };
        this.updateConversationSettings(changedSettings);
    }

    changeDocuments(selected_documents: string[]) {
        let changedSettings = { selected_documents };
        this.updateConversationSettings(changedSettings);
    }

    availablePrompts(allChains: Chain[], chain: string) {
        return allChains.find((c) => c.path === chain)?.prompt_names || [];
    }

    availableTools(allChains: Chain[], chain: string) {
        return allChains.find((c) => c.path === chain)?.tool_names || [];
    }

    supportsDocumentUpload(allChains: Chain[], chain: string) {
        return (
            allChains.find((c) => c.path === chain)?.supports_documents || false
        );
    }

    onFileUploaded($event: FileList) {
        console.debug("File uploaded", $event);
        let conversation_uuid = this.conversation()?.uuid;
        if (conversation_uuid) {
            this.loadDocuments();
        }
    }

    deleteDocument(document: Document) {
        console.debug("Delete document", document);
        let conversation_uuid = this.conversation()?.uuid;
        if (!conversation_uuid) {
            console.error("No conversation selected");
            return;
        }
        this.conversationService
            .deleteDocument(conversation_uuid, document.uuid)
            .subscribe((success) => {
                if (success) {
                    console.debug("Document deleted", document);
                    this.loadDocuments();
                } else {
                    console.error("Failed to delete document", document);
                }
            });
    }

    private loadDocuments() {
        let conversation_uuid = this.conversation()?.uuid;
        if (!conversation_uuid) return;
        this.documents =
            this.conversationService.getDocuments(conversation_uuid);
        this.changeDetectorRef.detectChanges();
    }

    private updateConversationSettings(changedSettings: ConversationSettings) {
        console.debug("Update conversation settings", changedSettings);
        let uuid = this.conversation()?.uuid;
        if (!uuid) return;
        this.conversationService
            .updateSettings(uuid, changedSettings)
            .subscribe((c) => {
                console.debug("Updated conversation settings", c);
                this.conversation.set(c);
            });
    }
}
