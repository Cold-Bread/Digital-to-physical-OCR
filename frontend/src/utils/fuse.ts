import Fuse from "fuse.js";
import { Patient, OCRResult } from "../types/backendResponse";

// --- Fuzzy matching function ---
export const getBoxRowClass = (
	patient: Patient,
	boxData: Patient[],
	ocrData: OCRResult[]
): string => {
	if (!patient || !patient.name) return "row-no-match";

	// Fuzzy matching setup
	const fuseOptions = {
		keys: ["name", "dob"],
		threshold: 0.3, // adjust for strictness
		includeScore: true,
	};
	const fuse = new Fuse(boxData, fuseOptions);

	let bestScore = 1; // lower = better

	for (const ocr of ocrData) {
		// Track scores separately
		let scores: number[] = [];

		// --- Name matching ---
		if (ocr.name) {
			const nameResults = fuse.search(ocr.name);
			if (nameResults.length > 0) {
				scores.push(nameResults[0].score ?? 1);
			}
		}

		// --- DOB matching ---
		if (ocr.dob) {
			const dobResults = fuse.search(ocr.dob);
			if (dobResults.length > 0) {
				scores.push(dobResults[0].score ?? 1);
			}
		}

		// Keep the best score from this OCR entry
		if (scores.length > 0) {
			const minScore = Math.min(...scores);
			if (minScore < bestScore) {
				bestScore = minScore;
			}
		}
	}

	// Classify match strength
	if (bestScore < 0.2) return "row-match"; // strong match
	if (bestScore < 0.4) return "row-partial-match"; // fuzzy but plausible
	return "row-no-match"; // nothing close
};
