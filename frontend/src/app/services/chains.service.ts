import { Injectable } from "@angular/core";
import { environment } from "../../environments/environment";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { Chain } from "../models/chain";

@Injectable({
    providedIn: "root",
})
export class ChainsService {
    backend_url = environment.backend_base_url;

    constructor(private http: HttpClient) {}

    public getAllChains(): Observable<Chain[]> {
        console.debug("Getting all chains");
        return this.http.get<Chain[]>(`${this.backend_url}/chains`);
    }
}
