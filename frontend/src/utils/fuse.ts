import Fuse from "fuse.js";
import { Patient, OCRResult } from "../types/backendResponse";

// --- Fuzzy matching function ---
export const getBoxRowClass = (
	patient: Patient,
	boxData: Patient[], // Keep for interface consistency even if unused
	ocrData: OCRResult[]
): string => {
	if (!patient || !patient.name) return "row-no-match";

	// Fuzzy matching setup - search within OCR data for matches to this patient
	const fuseOptions = {
		keys: ["name", "dob"],
		threshold: 0.4, // adjust for strictness (0.4 = more lenient than before)
		includeScore: true,
	};
	const fuse = new Fuse(ocrData, fuseOptions);

	let bestScore = 1; // lower = better
	let hasNameMatch = false;
	let hasDobMatch = false;

	// Search for this patient's name in OCR results
	if (patient.name) {
		const nameResults = fuse.search(patient.name);
		if (nameResults.length > 0) {
			const nameScore = nameResults[0].score ?? 1;
			if (nameScore < bestScore) {
				bestScore = nameScore;
				hasNameMatch = true;
			}
		}
	}

	// Search for this patient's DOB in OCR results
	if (patient.dob) {
		const dobResults = fuse.search(patient.dob);
		if (dobResults.length > 0) {
			const dobScore = dobResults[0].score ?? 1;
			if (dobScore < bestScore) {
				bestScore = dobScore;
				hasDobMatch = true;
			}
		}
	}

	// Enhanced classification considering both name and DOB matches
	if (bestScore < 0.15) return "row-match"; // very strong match
	if (bestScore < 0.3 && (hasNameMatch || hasDobMatch)) return "row-match"; // good match with either field
	if (bestScore < 0.4) return "row-partial-match"; // fuzzy but plausible
	return "row-no-match"; // nothing close
};
