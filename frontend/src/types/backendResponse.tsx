export interface OCRResult {
	name: string;
	dob: string;
	last_visit: string;
}

export interface Patient extends OCRResult {
	taken_from: string;
	placed_in: string;
	to_shred: boolean;
	date_shredded: string;
}

export interface BackendResponse {
	ocr1: OCRResult;
	ocr2: OCRResult;
	ocr3: OCRResult;
	finalResult: OCRResult;
	patient: Patient;
}
