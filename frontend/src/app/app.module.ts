import {
    APP_INITIALIZER,
    NgModule,
    provideExperimentalZonelessChangeDetection,
} from "@angular/core";
import { BrowserModule } from "@angular/platform-browser";

import { AppRoutingModule } from "./app-routing.module";
import { AppComponent } from "./app.component";
import { provideAnimationsAsync } from "@angular/platform-browser/animations/async";
import {
    KeycloakAngularModule,
    KeycloakBearerInterceptor,
    KeycloakService,
} from "keycloak-angular";
import {
    HTTP_INTERCEPTORS,
    provideHttpClient,
    withInterceptorsFromDi,
} from "@angular/common/http";
import { environment } from "../environments/environment";
import { CommonModule } from "@angular/common";
import {
    MatExpansionPanel,
    MatExpansionPanelHeader,
    MatExpansionPanelTitle,
} from "@angular/material/expansion";
import { MatLabel } from "@angular/material/form-field";
import { MatRadioButton, MatRadioGroup } from "@angular/material/radio";
import { ChatAreaComponent } from "./components/chatarea/chat-area.component";
import { SidebarComponent } from "./components/sidebar/sidebar.component";
import { MarkdownModule } from "ngx-markdown";


// This function initializes Keycloak with the provided configuration.
// Use it only if you don't want to force a full login after reloading the page.
//function initializeKeycloak(keycloak: KeycloakService) {
//    return () =>
//        keycloak.init({
//            config: {
//                url: "http://iai-ml4home028.iai.kit.edu/auth",
//                realm: "chatbot",
//                clientId: "oauth",
//            },
//            initOptions: {
//                onLoad: "check-sso",
//                silentCheckSsoRedirectUri: `${window.location.origin}/assets/silent-check-sso.html`,
//            },
//            shouldAddToken: (r) => {
//                return r.urlWithParams.includes(environment.backend_base_url);
//            },
//            enableBearerInterceptor: true,
//        });
//}


// This function initializes Keycloak with the provided configuration.
// Use it only if you want to force a full login every time the app starts.
function initializeKeycloak(keycloak: KeycloakService) {
    console.log("Initializing Keycloak with login-required"); 
    console.log(environment);
    return () =>
        keycloak.init({
            config: {
                url: "http://iai-ml4home028.iai.kit.edu/auth",
                realm: "chatbot",
                clientId: "oauth",
            },
            initOptions: {
                onLoad: "login-required", // ← this forces full login
            },
            enableBearerInterceptor: true,
        });
}



@NgModule({
    declarations: [AppComponent],
    imports: [
        CommonModule,
        BrowserModule,
        AppRoutingModule,
        KeycloakAngularModule,
        MatExpansionPanel,
        MatExpansionPanelHeader,
        MatExpansionPanelTitle,
        MatLabel,
        MatRadioButton,
        MatRadioGroup,
        ChatAreaComponent,
        SidebarComponent,
        MarkdownModule.forRoot(),
    ],
    providers: [
        provideExperimentalZonelessChangeDetection(),
        provideAnimationsAsync(),
        {
            provide: APP_INITIALIZER,
            useFactory: initializeKeycloak,
            multi: true,
            deps: [KeycloakService],
        },
        {
            provide: HTTP_INTERCEPTORS,
            useClass: KeycloakBearerInterceptor,
            multi: true,
        },
        provideHttpClient(withInterceptorsFromDi()),
    ],
    bootstrap: [AppComponent],
    exports: [],
})
export class AppModule {}
