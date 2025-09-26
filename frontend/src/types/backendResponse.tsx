export interface OCRResult {
	id: string; // Unique identifier for each OCR result
	name: string;
	dob: string | null;
	score?: number; // Confidence score from OCR is optional
	isPotentialDuplicate?: boolean;
	duplicateGroupId?: string;
	isResolved?: boolean; // Whether this duplicate has been resolved
	imageSource?: string; // Which image this result came from
	matchedPatientIndex?: number; // Index of the patient this result was matched to
}

export interface Patient {
	name: string;
	dob: string;
	year_joined: number;
	last_dos: number;
	shred_year: number;
	is_child_when_joined: boolean;
	box_number: string;
}

export interface BackendResponse {
	paddleOCR: OCRResult[];
}

// Separate type for box response since it's a different endpoint
export type BoxResponse = Patient[];

export interface OCRGroup {
	id: string;
	results: OCRResult[];
	isResolved: boolean;
}
