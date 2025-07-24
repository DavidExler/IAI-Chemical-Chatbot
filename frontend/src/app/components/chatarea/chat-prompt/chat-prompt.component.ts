import { Component, input, output } from "@angular/core";
import {
    MatFormField,
    MatLabel,
    MatSuffix,
} from "@angular/material/form-field";
import { FormsModule } from "@angular/forms";
import { MatIcon } from "@angular/material/icon";
import { MatButton, MatIconButton } from "@angular/material/button";
import { MatInput } from "@angular/material/input";
import { CdkTextareaAutosize } from "@angular/cdk/text-field";

@Component({
    selector: "app-chat-prompt",
    standalone: true,
    imports: [
        MatFormField,
        FormsModule,
        MatIcon,
        MatIconButton,
        MatInput,
        MatLabel,
        MatButton,
        MatSuffix,
        CdkTextareaAutosize,
    ],
    templateUrl: "./chat-prompt.component.html",
    styleUrl: "./chat-prompt.component.scss",
})
export class ChatPromptComponent {
    disabled = input<boolean>(true);
    generating = input<boolean>(true);

    onPrompt = output<string | null>();

    doPrompt(value: string | null) {
        if (this.disabled()) {
            this.onPrompt.emit(null);
            return;
        }
        this.onPrompt.emit(value);
    }
}
