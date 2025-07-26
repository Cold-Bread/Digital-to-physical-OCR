export interface OCRData {
	name: string;
	DOB: string;
	lastVisit: string;
}

export interface FinalResult extends OCRData {}

export interface PatientInfo extends OCRData {
	taken_from: string;
	placed_in: string;
	to_shred: boolean;
	date_shredded: string;
}

export interface BackendResponse {
	ocr1: OCRData;
	ocr2: OCRData;
	ocr3: OCRData;
	finalResult: FinalResult;
	patient: PatientInfo;
}
