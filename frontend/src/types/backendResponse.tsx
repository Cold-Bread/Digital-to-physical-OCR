export interface OCRResult {
    name: string;
    dob: string;
}

export interface Patient extends OCRResult {
    year_joined: number;
    last_dos: number;
    shred_year: number;
    is_child_when_joined: boolean;
    box_number: string;
}

export interface BackendResponse {
    ocr1: OCRResult[];
}

// Separate type for box response since it's a different endpoint
export type BoxResponse = Patient[];
