import { create } from "zustand";
import { BackendResponse } from "../types/types";

interface OCRStore {
	// Original backend response
	response: BackendResponse | null;
	setResponse: (resp: BackendResponse) => void;

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

	// Image blobs
	originalImage: string | null;
	setOriginalImage: (img: string | null) => void;

	enhancedImage: string | null;
	setEnhancedImage: (img: string | null) => void;

	// Reset function for zero-state
	resetAll: () => void;
}

export const useOCRStore = create<OCRStore>((set) => ({
	response: null,
	setResponse: (resp) => set({ response: resp }),

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

	originalImage: null,
	setOriginalImage: (img) => set({ originalImage: img }),

	enhancedImage: null,
	setEnhancedImage: (img) => set({ enhancedImage: img }),

	resetAll: () =>
		set({
			response: null,
			editableText: "Sample Editable LLM Output",
			ocr1: "Sample OCR Output 1",
			ocr2: "Sample OCR Output 2",
			ocr3: "Sample OCR Output 3",
			finalOutput: "Sample LLM Final Output",
			originalImage: null,
			enhancedImage: null,
		}),
}));
