export interface OCRResult {
	name: string;
	dob: string | null;
}

export interface Patient extends OCRResult {
	year_joined: number;
	last_dos: number;
	shred_year: number;
	is_child_when_joined: number;
	box_number: string;
}

export interface BackendResponse {
	ocr1: OCRResult[];
	ocr2: OCRResult[];
	ocr3: OCRResult[];
	finalResult: OCRResult;
}
