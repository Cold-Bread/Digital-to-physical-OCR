import { create } from "zustand";
import { BackendResponse } from "../types/backendResponse";

interface OCRStore {
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

	ocr2: string;
	setOCR2: (text: string) => void;

	ocr3: string;
	setOCR3: (text: string) => void;

	// LLM outputs
	finalOutput: string;
	setFinalOutput: (text: string) => void;

	// Reset function for zero-state
	resetAll: () => void;
}

export const useOCRStore = create<OCRStore>((set) => ({
	ocrResponse: null,
	setOCRResponse: (resp) => set({ ocrResponse: resp }),

	patientList: [],
	setPatientList: (list) => set({ patientList: list }),

	editableText: "",
	setEditableText: (text) => set({ editableText: text }),

	ocr1: "Sample OCR Output 1",
	setOCR1: (text) => set({ ocr1: text }),

	ocr2: "Sample OCR Output 2",
	setOCR2: (text) => set({ ocr2: text }),

	ocr3: "Sample OCR Output 3",
	setOCR3: (text) => set({ ocr3: text }),

	finalOutput: "Sample LLM Final Output",
	setFinalOutput: (text) => set({ finalOutput: text }),

	resetAll: () =>
		set({
			ocrResponse: null,
			patientList: [],
			editableText: "Sample Editable LLM Output",
			ocr1: "Sample OCR Output 1",
			ocr2: "Sample OCR Output 2",
			ocr3: "Sample OCR Output 3",
			finalOutput: "Sample LLM Final Output",
		}),
}));
