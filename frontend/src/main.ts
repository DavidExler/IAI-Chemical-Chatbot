import { AppModule } from "./app/app.module";
import { platformBrowserDynamic } from "@angular/platform-browser-dynamic";

platformBrowserDynamic()
    .bootstrapModule(AppModule, { ngZone: "noop" })
    .catch((err) => console.error(err));
