export interface Feedback {
    type: "up" | "down";
    expected_answer?: string;
    feedback?: string;
}
