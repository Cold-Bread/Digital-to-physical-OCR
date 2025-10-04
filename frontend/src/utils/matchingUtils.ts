import Fuse from "fuse.js";
import { Patient, OCRResult } from "../types/Types";

// Enhanced match types for better clarity
export type MatchQuality = "full" | "partial" | "none";
export type MatchResult = {
	quality: MatchQuality;
	score: number;
	ocrResult?: OCRResult;
	confidence: number;
};

// --- Name normalization functions ---
/**
 * Normalize a name to handle different formats:
 * - "LastName, FirstName" → "firstname lastname"
 * - "FirstName LastName" → "firstname lastname"
 * - Handles multiple words in names (like "Dela Cruz, Rachel")
 */
export const normalizeName = (name: string): string => {
	if (!name || typeof name !== "string") return "";

	// Clean up the name
	let cleaned = name.trim().toLowerCase();

	// Handle "LastName, FirstName" format
	if (cleaned.includes(",")) {
		const parts = cleaned
			.split(",")
			.map((part) => part.trim())
			.filter((part) => part.length > 0);
		if (parts.length >= 2) {
			// Reverse: "lastname, firstname" → "firstname lastname"
			const lastName = parts[0];
			const firstName = parts[1];
			cleaned = `${firstName} ${lastName}`;
		}
	}

	// Remove extra whitespace and normalize
	cleaned = cleaned.replace(/\s+/g, " ").trim();

	return cleaned;
};

/**
 * Create variations of a name for better matching
 * Returns array of normalized name variations to try
 */
export const createNameVariations = (name: string): string[] => {
	if (!name) return [];

	const variations = new Set<string>();
	const normalized = normalizeName(name);
	variations.add(normalized);

	// Add the original normalized form
	const words = normalized.split(" ").filter((word) => word.length > 0);

	if (words.length >= 2) {
		// Add "lastname firstname" variation (reverse)
		const reversed = words.slice(1).join(" ") + " " + words[0];
		variations.add(reversed);

		// Add partial matches (just first and last name for multi-word names)
		if (words.length > 2) {
			variations.add(`${words[0]} ${words[words.length - 1]}`); // first + last
			variations.add(`${words[words.length - 1]} ${words[0]}`); // last + first
		}
	}

	return Array.from(variations);
};

// --- Enhanced matching algorithm with improved scoring ---
export const findBestMatch = (
	patient: Patient,
	ocrResults: OCRResult[]
): MatchResult => {
	if (!patient || !patient.name || !ocrResults.length) {
		return { quality: "none", score: 1, confidence: 0 };
	}

	console.log(
		`🔍 Finding match for patient: "${patient.name}" | DOB: "${patient.dob}"`
	);

	// Create normalized versions of OCR results for better matching
	const normalizedOCRResults = ocrResults.map((ocr) => {
		const normalized = normalizeName(ocr.name);
		if (normalized !== ocr.name.toLowerCase().trim()) {
			console.log(`  🔄 OCR name normalized: "${ocr.name}" → "${normalized}"`);
		}
		return {
			...ocr,
			normalizedName: normalized,
			originalName: ocr.name, // Keep original for reference
		};
	});

	// Separate search configurations for names and DOBs
	const nameSearchOptions = {
		keys: ["normalizedName"], // Search using normalized names
		threshold: 0.6, // More lenient for names (handles format differences)
		includeScore: true,
	};

	const dobSearchOptions = {
		keys: ["dob"],
		threshold: 0.4, // Stricter for DOBs (more precise matching needed)
		includeScore: true,
	};

	const nameFuse = new Fuse(normalizedOCRResults, nameSearchOptions);
	const dobFuse = new Fuse(normalizedOCRResults, dobSearchOptions);

	let bestMatch: OCRResult | undefined;
	let bestScore = 1;
	let matchType = "none";
	let nameMatchScore = 1;
	let dobMatchScore = 1;

	// PRIORITIZED MATCHING STRATEGY WITH NAME NORMALIZATION:
	// 1. Look for name matches using normalized variations
	let nameMatches: any[] = [];
	if (patient.name) {
		const patientNameVariations = createNameVariations(patient.name);
		console.log(
			`  🔄 Patient name variations: [${patientNameVariations
				.map((n) => `"${n}"`)
				.join(", ")}]`
		);

		// Try each name variation and find the best match
		let bestNameMatch: any = null;
		let bestNameScore = 1;

		patientNameVariations.forEach((nameVariation) => {
			const matches = nameFuse.search(nameVariation);
			if (matches.length > 0) {
				const score = matches[0].score ?? 1;
				if (score < bestNameScore) {
					bestNameScore = score;
					bestNameMatch = matches[0];
				}
			}
		});

		if (bestNameMatch) {
			nameMatches = [bestNameMatch];
			nameMatchScore = bestNameScore;
			console.log(
				`  📝 Best name match: "${
					bestNameMatch.item.name
				}" (score: ${nameMatchScore.toFixed(3)})`
			);
		}
	}

	// 2. Look for DOB matches
	let dobMatches: any[] = [];
	if (patient.dob) {
		dobMatches = dobFuse.search(patient.dob);
		if (dobMatches.length > 0) {
			dobMatchScore = dobMatches[0].score ?? 1;
			console.log(
				`  📅 Best DOB match: "${
					dobMatches[0].item.dob
				}" (score: ${dobMatchScore.toFixed(3)})`
			);
		}
	}

	// 3. IMPROVED MATCHING LOGIC: Prioritize name matches, but consider combined evidence
	if (nameMatches.length > 0 && dobMatches.length > 0) {
		// Both name and DOB matches exist - check if they're the same OCR result
		const nameMatch = nameMatches[0].item;
		const dobMatch = dobMatches[0].item;

		if (nameMatch.id === dobMatch.id) {
			// Perfect! Same OCR result matches both name and DOB
			bestMatch = nameMatch;
			bestScore = Math.min(nameMatchScore, dobMatchScore); // Take the better score
			matchType = "both";
			console.log(
				`  ✅ PERFECT MATCH: Same OCR result matches both name and DOB`
			);
		} else {
			// Different OCR results - prioritize name match if it's reasonably good
			if (nameMatchScore < 0.4) {
				// Good name match - use it
				bestMatch = nameMatch;
				bestScore = nameMatchScore;
				matchType = "name-priority";
				console.log(
					`  📝 Using NAME match (good score: ${nameMatchScore.toFixed(3)})`
				);
			} else if (dobMatchScore < 0.2) {
				// Excellent DOB match, but poor name match - use DOB
				bestMatch = dobMatch;
				bestScore = dobMatchScore;
				matchType = "dob-priority";
				console.log(
					`  📅 Using DOB match (excellent score: ${dobMatchScore.toFixed(3)})`
				);
			} else {
				// Both matches are mediocre - use the better one
				if (nameMatchScore <= dobMatchScore) {
					bestMatch = nameMatch;
					bestScore = nameMatchScore;
					matchType = "name-fallback";
					console.log(`  📝 Using NAME match (better of two mediocre scores)`);
				} else {
					bestMatch = dobMatch;
					bestScore = dobMatchScore;
					matchType = "dob-fallback";
					console.log(`  📅 Using DOB match (better of two mediocre scores)`);
				}
			}
		}
	} else if (nameMatches.length > 0) {
		// Only name match
		bestMatch = nameMatches[0].item;
		bestScore = nameMatchScore;
		matchType = "name-only";
		console.log(`  📝 Using NAME-only match`);
	} else if (dobMatches.length > 0) {
		// Only DOB match
		bestMatch = dobMatches[0].item;
		bestScore = dobMatchScore;
		matchType = "dob-only";
		console.log(`  📅 Using DOB-only match`);
	}

	// Determine match quality based on score and match type
	const confidence = Math.max(0, (1 - bestScore) * 100);
	let quality: MatchQuality = "none";

	if (matchType === "both") {
		// Both name and DOB match the same OCR result
		quality = "full";
	} else if (matchType === "name-priority" || matchType === "name-only") {
		// Name-based matches
		if (bestScore < 0.2) quality = "full";
		else if (bestScore < 0.4) quality = "partial";
	} else if (matchType === "dob-priority" || matchType === "dob-only") {
		// DOB-based matches (stricter criteria)
		if (bestScore < 0.1) quality = "full";
		else if (bestScore < 0.3) quality = "partial";
	} else if (matchType.includes("fallback")) {
		// Fallback matches (even stricter)
		if (bestScore < 0.3) quality = "partial";
	}

	console.log(
		`  🎯 Final result: ${quality} match (${matchType}, score: ${bestScore.toFixed(
			3
		)}, confidence: ${confidence.toFixed(1)}%)`
	);

	// Extract original OCR result (handle both normalized and original results)
	const originalOCRResult = bestMatch
		? {
				id: bestMatch.id,
				name: (bestMatch as any).originalName || bestMatch.name,
				dob: bestMatch.dob,
				score: bestMatch.score,
				imageSource: bestMatch.imageSource,
				matchedPatientIndex: bestMatch.matchedPatientIndex,
		  }
		: undefined;

	return {
		quality,
		score: bestScore,
		ocrResult: originalOCRResult,
		confidence,
	};
};

// --- Legacy function for backward compatibility ---
export const getBoxRowClass = (
	patient: Patient,
	_boxData: Patient[], // Keep for interface consistency (underscore to indicate unused)
	ocrData: OCRResult[]
): string => {
	const match = findBestMatch(patient, ocrData);
	switch (match.quality) {
		case "full":
			return "row-match";
		case "partial":
			return "row-partial-match";
		default:
			return "row-no-match";
	}
};

// --- New function to create aligned OCR table ---
export const createAlignedOCRTable = (
	patients: Patient[],
	ocrResults: OCRResult[]
): (OCRResult | null)[] => {
	console.log("🔄 Creating aligned OCR table", {
		patients: patients.length,
		ocrResults: ocrResults.length,
	});

	// Create table with same length as patients table
	const alignedTable: (OCRResult | null)[] = new Array(patients.length).fill(
		null
	);
	const usedOCRResults = new Set<string>();

	// Track match statistics for debugging
	const matchStats = {
		fullMatches: 0,
		partialMatches: 0,
		noMatches: 0,
		conflicts: 0, // When multiple patients want the same OCR result
	};

	// First pass: Find all potential matches and resolve conflicts
	const potentialMatches: { patientIndex: number; match: MatchResult }[] = [];

	patients.forEach((patient, index) => {
		const match = findBestMatch(patient, ocrResults);
		if (match.quality !== "none" && match.ocrResult) {
			potentialMatches.push({ patientIndex: index, match });
		}
	});

	// Sort potential matches by quality (full matches first) and then by score (lower is better)
	potentialMatches.sort((a, b) => {
		if (a.match.quality === "full" && b.match.quality !== "full") return -1;
		if (b.match.quality === "full" && a.match.quality !== "full") return 1;
		return a.match.score - b.match.score; // Lower score = better match
	});

	// Assign matches, avoiding conflicts
	potentialMatches.forEach(({ patientIndex, match }) => {
		if (match.ocrResult && !usedOCRResults.has(match.ocrResult.id)) {
			alignedTable[patientIndex] = match.ocrResult;
			usedOCRResults.add(match.ocrResult.id);

			if (match.quality === "full") matchStats.fullMatches++;
			else if (match.quality === "partial") matchStats.partialMatches++;

			console.log(
				`✅ Assigned ${match.quality.toUpperCase()} match: Patient ${patientIndex} ("${
					patients[patientIndex].name
				}") ← OCR ("${
					match.ocrResult.name
				}", confidence: ${match.confidence.toFixed(1)}%)`
			);
		} else if (match.ocrResult && usedOCRResults.has(match.ocrResult.id)) {
			// Conflict detected
			matchStats.conflicts++;
			console.log(
				`⚠️  Conflict: Patient ${patientIndex} ("${patients[patientIndex].name}") wanted OCR result "${match.ocrResult.name}" but it was already assigned`
			);
		}
	});

	// Count patients with no matches
	matchStats.noMatches =
		patients.length - matchStats.fullMatches - matchStats.partialMatches;

	// Second pass: Fill remaining empty slots with unmatched OCR results
	const unusedOCRResults = ocrResults.filter(
		(ocr) => !usedOCRResults.has(ocr.id)
	);
	let ocrIndex = 0;

	for (
		let i = 0;
		i < alignedTable.length && ocrIndex < unusedOCRResults.length;
		i++
	) {
		if (alignedTable[i] === null) {
			alignedTable[i] = unusedOCRResults[ocrIndex];
			console.log(
				`📝 Placed unmatched OCR result at empty slot ${i}: "${unusedOCRResults[ocrIndex].name}"`
			);
			ocrIndex++;
		}
	}

	// Third pass: If we have more OCR results than empty slots, extend the table
	while (ocrIndex < unusedOCRResults.length) {
		alignedTable.push(unusedOCRResults[ocrIndex]);
		console.log(
			`➕ Extended table for additional OCR result: "${unusedOCRResults[ocrIndex].name}"`
		);
		ocrIndex++;
	}

	// Final statistics
	console.log("🎯 Aligned table created with match statistics:", {
		totalSlots: alignedTable.length,
		filledSlots: alignedTable.filter((item) => item !== null).length,
		emptySlots: alignedTable.filter((item) => item === null).length,
		matchQuality: {
			fullMatches: matchStats.fullMatches,
			partialMatches: matchStats.partialMatches,
			noMatches: matchStats.noMatches,
			conflicts: matchStats.conflicts,
		},
	});

	return alignedTable;
};
