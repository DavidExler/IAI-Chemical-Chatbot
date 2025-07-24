import { Injectable } from "@angular/core";

@Injectable({
    providedIn: "root",
})
export class LocalstorageService {
    public write(key: string, value: any) {
        localStorage.setItem(key, JSON.stringify(value));
    }

    public read(key: string): any {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
    }
}
