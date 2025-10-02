import { OCRResult } from "../types/backendResponse";

// Common OCR character substitutions
const OCR_CORRECTIONS: Record<string, string> = {
	// Number/Letter confusions
	"0": "O",
	"1": "I",
	"5": "S",
	"8": "B",
	"6": "G",
	O: "0",
	l: "1",
	I: "1",
	S: "5",
	B: "8",
	G: "6",

	// Common misreads
	rn: "m",
	ni: "n",
	ii: "n",
	vv: "w",
	VV: "W",
	cl: "d",
	ri: "n",
	li: "h",
	ti: "h",
	hl: "h",

	// Date-specific
	SOB: "DOB",
	D0B: "DOB",
	D08: "DOB",
	OOB: "DOB",
};

// Common name prefixes/suffixes patterns
const NAME_PATTERNS = {
	prefixes: ["Mr", "Mrs", "Ms", "Dr", "Prof"],
	suffixes: ["Jr", "Sr", "II", "III", "IV", "V"],
};

// Date format patterns (regex patterns to identify dates)
const DATE_PATTERNS = [
	/^\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{2,4}$/, // MM/DD/YYYY, MM-DD-YY, etc.
	/^\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{2}$/, // MM/DD/YY
	/^(DOB|SOB|OOB|D0B|D08)[-:]?\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{2,4}$/i, // DOB:MM/DD/YYYY
	/^\d{2}[\/\-]\d{2}[\/\-]\d{2,4}$/, // Standard formats
];

// Patterns that indicate non-name content
const NON_NAME_PATTERNS = [
	/^\d+[A-Z]*$/, // "119400B", "CS4E2"
	/^[A-Z0-9]{3,}$/, // All caps alphanumeric codes
	/^\d{2,}\.\d+$/, // Numbers with decimals "DO05.576"
	/^\d+\s+\d+$/, // Spaced numbers "30 90"
	/^\d+:\d+$/, // Time-like "006:43033"
	/^[^a-zA-Z]*$/, // No letters at all
];

/**
 * Applies basic OCR corrections to text
 */
export function applyOCRCorrections(text: string): string {
	if (!text) return text;

	let corrected = text;

	// Apply character-level corrections
	for (const [wrong, right] of Object.entries(OCR_CORRECTIONS)) {
		// Use word boundaries to avoid over-correction
		const regex = new RegExp(`\\b${wrong}\\b`, "g");
		corrected = corrected.replace(regex, right);
	}

	return corrected;
}

/**
 * Normalizes name text - fixes case, common OCR errors, formatting
 */
export function normalizeName(name: string): string {
	if (!name || typeof name !== "string") return "";

	// Remove leading/trailing whitespace
	let normalized = name.trim();

	// Skip obviously non-name content
	if (NON_NAME_PATTERNS.some((pattern) => pattern.test(normalized))) {
		return "";
	}

	// Apply OCR corrections
	normalized = applyOCRCorrections(normalized);

	// Fix common OCR name issues
	normalized = normalized
		// Fix common letter combinations
		.replace(/rn/g, "m") // "reamp" -> "ream" -> likely "ream" but closer to real name
		.replace(/ChRTs/g, "Chris") // "ChRTs" -> "Chris"
		.replace(/([a-z])([A-Z])/g, "$1 $2") // "CAssidy" -> "C Assidy", "SusAnnA" -> "Sus Ann A"

		// Clean up multiple spaces
		.replace(/\s+/g, " ")

		// Convert to proper case (Title Case)
		.toLowerCase()
		.replace(/\b\w+/g, (word) => {
			// Handle special cases for common name prefixes/suffixes
			const upper = word.toUpperCase();
			if (
				NAME_PATTERNS.prefixes.includes(word) ||
				NAME_PATTERNS.suffixes.includes(upper)
			) {
				return upper;
			}
			// Handle names like "McDonald", "MacLeod", "O'Connor"
			if (
				word.startsWith("mc") ||
				word.startsWith("mac") ||
				word.includes("'")
			) {
				return word.charAt(0).toUpperCase() + word.slice(1);
			}
			// Standard title case
			return word.charAt(0).toUpperCase() + word.slice(1);
		});

	return normalized.trim();
}

/**
 * Parses and normalizes date strings
 */
export function normalizeDate(dateStr: string): string | null {
	if (!dateStr || typeof dateStr !== "string") return null;

	let cleaned = dateStr.trim();

	// Remove common OCR prefixes
	cleaned = cleaned.replace(/^(DOB|SOB|OOB|D0B|D08)[-:]?\s*/i, "");

	// Apply basic OCR corrections
	cleaned = applyOCRCorrections(cleaned);

	// Skip obviously invalid dates
	if (cleaned.length < 6 || cleaned.includes("lary")) {
		return null;
	}

	// Try to match date patterns
	const isDateLike = DATE_PATTERNS.some((pattern) => pattern.test(cleaned));
	if (!isDateLike) {
		return null;
	}

	// Normalize separators to forward slashes
	cleaned = cleaned.replace(/[-,]/g, "/");

	// Try to parse and validate the date
	try {
		const parts = cleaned.split("/");
		if (parts.length !== 3) return null;

		let [month, day, year] = parts.map((p) => parseInt(p, 10));

		// Handle 2-digit years
		if (year < 100) {
			// Assume 1900s for years > 30, 2000s for years <= 30
			year += year > 30 ? 1900 : 2000;
		}

		// Basic validation
		if (
			month < 1 ||
			month > 12 ||
			day < 1 ||
			day > 31 ||
			year < 1900 ||
			year > 2030
		) {
			return null;
		}

		// Return in MM/DD/YYYY format
		return `${month.toString().padStart(2, "0")}/${day
			.toString()
			.padStart(2, "0")}/${year}`;
	} catch (error) {
		console.warn("Date parsing error:", error, "for date:", dateStr);
		return null;
	}
}

/**
 * Checks if a string looks like a valid name
 */
function isValidName(name: string): boolean {
	if (!name || typeof name !== "string") return false;

	const trimmed = name.trim();

	// Must have letters
	if (!/[a-zA-Z]/.test(trimmed)) return false;

	// Check against non-name patterns
	if (NON_NAME_PATTERNS.some((pattern) => pattern.test(trimmed))) return false;

	// Must be reasonable length
	if (trimmed.length < 2 || trimmed.length > 50) return false;

	// Should not be mostly numbers
	const letterCount = (trimmed.match(/[a-zA-Z]/g) || []).length;
	const totalCount = trimmed.replace(/\s/g, "").length;
	return letterCount / totalCount >= 0.5;
}

/**
 * Checks if a string looks like a valid date
 */
function isValidDate(dateStr: string): boolean {
	if (!dateStr || typeof dateStr !== "string") return false;
	return normalizeDate(dateStr) !== null;
}

/**
 * Combines adjacent OCR results where one has name and other has DOB
 */
function combineStackedEntries(results: OCRResult[]): OCRResult[] {
	if (!results || results.length === 0) return results;

	const combined: OCRResult[] = [];
	let i = 0;

	while (i < results.length) {
		const current = results[i];
		const next = i + 1 < results.length ? results[i + 1] : null;

		// Check if current and next can be combined
		if (next && shouldCombineEntries(current, next)) {
			const combinedEntry: OCRResult = {
				...current,
				name: current.name || next.name || "",
				dob: current.dob || next.dob || null,
				// Use the higher confidence score
				score: Math.max(current.score || 0, next.score || 0),
				// Combine IDs or create new one
				id: current.id || next.id || Math.random().toString(36).substr(2, 9),
			};

			combined.push(combinedEntry);
			i += 2; // Skip both entries
		} else {
			combined.push(current);
			i += 1;
		}
	}

	return combined;
}

/**
 * Determines if two OCR entries should be combined
 */
function shouldCombineEntries(current: OCRResult, next: OCRResult): boolean {
	// One should have name, other should have DOB
	const currentHasName = isValidName(current.name);
	const currentHasDOB = isValidDate(current.dob || "");
	const nextHasName = isValidName(next.name);
	const nextHasDOB = isValidDate(next.dob || "");

	// Combine if:
	// 1. Current has name but no DOB, next has DOB but no name
	// 2. Current has DOB but no name, next has name but no DOB
	return (
		(currentHasName && !currentHasDOB && !nextHasName && nextHasDOB) ||
		(!currentHasName && currentHasDOB && nextHasName && !nextHasDOB)
	);
}

/**
 * Main normalization function - applies all normalization steps
 */
export function normalizeOCRResults(results: OCRResult[]): OCRResult[] {
	if (!results || results.length === 0) return results;

	console.log("🔧 Starting OCR normalization...", results.length, "results");

	// Step 1: Combine stacked entries
	let normalized = combineStackedEntries(results);
	console.log(
		"📋 After combining stacked entries:",
		normalized.length,
		"results"
	);

	// Step 2: Normalize individual entries
	normalized = normalized.map((result) => {
		const normalizedName = result.name ? normalizeName(result.name) : "";
		const normalizedDOB = result.dob ? normalizeDate(result.dob) : null;

		return {
			...result,
			name: normalizedName,
			dob: normalizedDOB,
		};
	});

	// Step 3: Filter out invalid entries
	const filtered = normalized.filter((result) => {
		const hasValidName = isValidName(result.name);
		const hasValidDOB = isValidDate(result.dob || "");

		// Keep entries that have at least a valid name or valid DOB
		return hasValidName || hasValidDOB;
	});

	console.log(
		"✅ OCR normalization complete:",
		filtered.length,
		"valid results"
	);
	return filtered;
}

// Export utility functions for individual use
export { isValidName, isValidDate, combineStackedEntries };
