import { create } from "zustand";
import {
	BackendResponse,
	BoxResponse,
	OCRResult,
} from "../types/backendResponse";
import { normalizeOCRResults } from "../utils/ocrNormalization";

type EditHistory = {
	patientList: BoxResponse;
	timestamp: number;
};

interface OCRStore {
	// OCR results from image processing
	ocrResponse: BackendResponse | null;
	allOCRResults: OCRResult[]; // All OCR results across all scans
	setOCRResponse: (resp: BackendResponse | null, imageSource: string) => void;
	addOCRResults: (results: OCRResult[], imageSource: string) => void;
	updateOCRResult: (id: string, updatedResult: Partial<OCRResult>) => void;

	// Patient list response from box search
	patientList: BoxResponse;
	setPatientList: (list: BoxResponse) => void;

	// Match tracking
	matchedResults: Map<number, OCRResult>; // patientIndex -> OCR result
	setMatch: (patientIndex: number, result: OCRResult) => void;
	removeMatch: (patientIndex: number) => void;

	// Box number management
	currentBoxNumber: string;
	setCurrentBoxNumber: (boxNumber: string) => void;
	applyBoxNumber: () => void; // Apply current box number to matched patients

	// Edit history
	history: EditHistory[];
	addToHistory: (list: BoxResponse) => void;
	undo: () => void;
	undoAll: () => void;

	// Loading state
	isLoading: boolean;
	setIsLoading: (loading: boolean) => void;

	// Reset function for zero-state
	resetAll: () => void;
}

// Simple logging wrapper for store updates
const logStoreUpdate = (actionName: string, payload?: any) => {
	if (process.env.NODE_ENV === "development") {
		console.log(`🏪 ${actionName}:`, payload);
	}
};

export const useOCRStore = create<OCRStore>((set, get) => ({
	// OCR state
	ocrResponse: null,
	allOCRResults: [],
	matchedResults: new Map(),
	currentBoxNumber: "",

	// Set OCR response and add results
	setOCRResponse: (resp, imageSource) => {
		set({ ocrResponse: resp });

		if (!resp) {
			console.warn("No OCR response provided");
			return;
		}

		let ocrArray = null;

		// Check for paddleOCR format
		if (resp.paddleOCR && Array.isArray(resp.paddleOCR)) {
			ocrArray = resp.paddleOCR;
		} else {
			// Fallback: check if response is directly an array
			if (Array.isArray(resp)) {
				ocrArray = resp;
			} else {
				console.warn("Unexpected OCR response format:", resp);
			}
		}

		if (ocrArray) {
			get().addOCRResults(ocrArray, imageSource);
		} else {
			console.warn("Invalid OCR response format - no OCR data array found");
		}
	},

	// Add new OCR results
	addOCRResults: (results, imageSource) => {
		logStoreUpdate("ADD_OCR_RESULTS", { count: results?.length, imageSource });
		if (!Array.isArray(results)) {
			console.warn("Results is not an array:", results);
			return;
		}

		const currentResults = [...get().allOCRResults];

		// Apply simplified normalization
		const normalizedResults = normalizeOCRResults(results);

		const newResults = normalizedResults
			.filter((result) => {
				// Basic filter - normalization already handles most of this
				const hasName = result && result.name && result.name.trim() !== "";
				const hasDob = result && result.dob && result.dob.trim() !== "";
				return result && typeof result === "object" && (hasName || hasDob);
			})
			.map((result) => ({
				...result,
				id: result.id || Math.random().toString(36).substr(2, 9),
				imageSource,
			}));

		set({
			allOCRResults: [...currentResults, ...newResults],
		});
		logStoreUpdate("OCR_RESULTS_ADDED", {
			totalCount: currentResults.length + newResults.length,
			newCount: newResults.length,
			normalizedCount: normalizedResults.length,
			originalCount: results.length,
		});
	},

	// Update an existing OCR result
	updateOCRResult: (id, updatedFields) => {
		const currentResults = [...get().allOCRResults];
		const index = currentResults.findIndex((r) => r.id === id);

		if (index !== -1) {
			currentResults[index] = {
				...currentResults[index],
				...updatedFields,
			};
			set({ allOCRResults: currentResults });
			console.log(`Updated OCR result ${id}:`, currentResults[index]);
		} else {
			console.warn(`OCR result with id ${id} not found`);
		}
	},

	// Match tracking
	setMatch: (patientIndex, result) => {
		const matches = new Map(get().matchedResults);
		matches.set(patientIndex, result);
		set({ matchedResults: matches });

		// Update the OCR result to mark it as matched
		const results = [...get().allOCRResults];
		const resultIndex = results.findIndex((r) => r.id === result.id);
		if (resultIndex !== -1) {
			results[resultIndex] = {
				...results[resultIndex],
				matchedPatientIndex: patientIndex,
			};
			set({ allOCRResults: results });
		}
	},

	removeMatch: (patientIndex) => {
		const matches = new Map(get().matchedResults);
		const removedMatch = matches.get(patientIndex);
		matches.delete(patientIndex);
		set({ matchedResults: matches });

		// Update the OCR result to remove the match
		if (removedMatch) {
			const results = [...get().allOCRResults];
			const resultIndex = results.findIndex((r) => r.id === removedMatch.id);
			if (resultIndex !== -1) {
				results[resultIndex] = {
					...results[resultIndex],
					matchedPatientIndex: undefined,
				};
				set({ allOCRResults: results });
			}
		}
	},

	// Box number management
	setCurrentBoxNumber: (boxNumber) => {
		set({ currentBoxNumber: boxNumber });
	},

	applyBoxNumber: () => {
		const boxNumber = get().currentBoxNumber;
		if (!boxNumber) return;

		const currentList = [...get().patientList];
		const matches = get().matchedResults;

		matches.forEach((_, patientIndex) => {
			if (currentList[patientIndex]) {
				currentList[patientIndex] = {
					...currentList[patientIndex],
					box_number: boxNumber,
				};
			}
		});

		set({ patientList: currentList });
		get().addToHistory(currentList);
	},

	// Patient list management
	patientList: [],
	setPatientList: (list) => {
		set({ patientList: list });
		get().addToHistory(list);
	},

	// History management
	history: [],
	addToHistory: (list) => {
		const currentHistory = get().history;
		set({
			history: [
				...currentHistory,
				{
					patientList: JSON.parse(JSON.stringify(list)),
					timestamp: Date.now(),
				},
			],
		});
	},
	undo: () => {
		const currentHistory = get().history;
		if (currentHistory.length > 1) {
			const newHistory = [...currentHistory];
			newHistory.pop();
			const previousState = newHistory[newHistory.length - 1];
			set({
				patientList: previousState.patientList,
				history: newHistory,
			});
		}
	},
	undoAll: () => {
		const currentHistory = get().history;
		if (currentHistory.length > 1) {
			const initialState = currentHistory[0];
			set({
				patientList: initialState.patientList,
				history: [initialState],
			});
		}
	},

	// Loading state
	isLoading: false,
	setIsLoading: (loading) => {
		set({ isLoading: loading });
	},

	// Reset everything
	resetAll: () => {
		set({
			ocrResponse: null,
			allOCRResults: [],
			matchedResults: new Map(),
			currentBoxNumber: "",
			patientList: [],
			isLoading: false,
			history: [],
		});
	},
}));
