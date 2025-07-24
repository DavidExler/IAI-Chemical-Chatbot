import { NgModule } from "@angular/core";
import { RouterModule, Routes } from "@angular/router";
import { AuthGuard } from "./guards/auth";
import { AppComponent } from "./app.component";

const routes: Routes = [
    {
        path: "",        
        canActivate: [AuthGuard],
        component: AppComponent,
    },
];

@NgModule({
    imports: [RouterModule.forRoot(routes)],
    exports: [RouterModule],
})
export class AppRoutingModule {}
