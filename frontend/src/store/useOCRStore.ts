import { create } from "zustand";
import { BackendResponse } from "../types/backendResponse";

type TextType = 'printed' | 'handwritten';

interface OCRStore {
	// Text type toggle
	textType: TextType;
	setTextType: (type: TextType) => void;

	// OCR and LLM response
	ocrResponse: BackendResponse | null;
	setOCRResponse: (resp: BackendResponse) => void;

	// Patient list response
	patientList: any[];
	setPatientList: (list: any[]) => void;

	// Editable text from LLM
	editableText: string;
	setEditableText: (text: string) => void;

	// OCR text outputs
	ocr1: string;
	setOCR1: (text: string) => void;

	// Reset function for zero-state
	resetAll: () => void;
}

export const useOCRStore = create<OCRStore>((set) => ({
	textType: 'printed',
	setTextType: (type) => set({ textType: type }),

	ocrResponse: null,
	setOCRResponse: (resp) => set({ ocrResponse: resp }),

	patientList: [],
	setPatientList: (list) => set({ patientList: list }),

	editableText: "",
	setEditableText: (text) => set({ editableText: text }),

	ocr1: "Sample OCR Output 1",
	setOCR1: (text) => set({ ocr1: text }),

	resetAll: () =>
		set({
			ocrResponse: null,
			patientList: [],
			editableText: "Sample Editable LLM Output",
			ocr1: "Sample OCR Output 1",
		}),
}));
