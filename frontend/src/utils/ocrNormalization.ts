import { OCRResult } from "../types/backendResponse";

/**
 * SIMPLIFIED OCR NORMALIZATION
 * Let Fuse.js handle fuzzy name matching - we just clean obvious garbage and normalize dates
 */

// Date format patterns
const DATE_PATTERNS = [
	/^\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{2,4}$/, // MM/DD/YYYY, MM-DD-YY, etc.
	/^(DOB|SOB|OOB|D0B|D08)[-:]?\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{2,4}$/i, // DOB:MM/DD/YYYY
	/^\d{1,2}[,]\d{1,2}[-]\d{1,2}[-]\d{2,4}$/, // Mixed separators like "13,6-29-77"
	/^\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{1,4}$/, // Flexible pattern for OCR errors
];

// Patterns that indicate complete garbage (not names)
const GARBAGE_PATTERNS = [
	/^\d+[A-Z]*$/, // "119400B", "CS4E2"
	/^\d{2,}\.\d+$/, // Numbers with decimals "DO05.576"
	/^\d+\s+\d+$/, // Spaced numbers "30 90"
	/^\d+:\d+$/, // Time-like "006:43033"
	/^[^a-zA-Z]*$/, // No letters at all
];

/**
 * Check if a name is obviously garbage (not a real name)
 */
function isGarbageName(name: string): boolean {
	if (!name || typeof name !== "string") return true;
	const trimmed = name.trim();

	// Must have some letters
	if (!/[a-zA-Z]/.test(trimmed)) return true;

	// Check against garbage patterns
	if (GARBAGE_PATTERNS.some((pattern) => pattern.test(trimmed))) return true;

	// Must be reasonable length
	if (trimmed.length < 2 || trimmed.length > 50) return true;

	return false;
}

/**
 * Basic date normalization - handle OCR prefixes and format
 */
function normalizeDate(dateStr: string): string | null {
	if (!dateStr || typeof dateStr !== "string") return null;

	let cleaned = dateStr.trim();
	console.log(`🗓️ Normalizing date: "${dateStr}" -> cleaned: "${cleaned}"`);

	// Remove common OCR prefixes (SOB -> DOB, etc.)
	cleaned = cleaned.replace(/^(DOB|SOB|OOB|D0B|D08)[-:]?\s*/i, "");
	console.log(`After prefix removal: "${cleaned}"`);

	// Skip obviously invalid dates
	if (
		cleaned.length < 5 ||
		cleaned.includes("lary") ||
		cleaned.includes("ary")
	) {
		console.log(`Skipping invalid date: "${cleaned}"`);
		return null;
	}

	// Normalize separators
	cleaned = cleaned.replace(/[,\-]/g, "/");
	console.log(`After separator normalization: "${cleaned}"`);

	// Check if it looks like a date
	const isDateLike = DATE_PATTERNS.some((pattern) => pattern.test(cleaned));
	console.log(`Date pattern match: ${isDateLike} for "${cleaned}"`);

	if (!isDateLike) {
		console.log(`No pattern match for: "${cleaned}"`);
		return null;
	}

	// Try to parse
	try {
		const parts = cleaned.split("/");
		if (parts.length !== 3) {
			console.log(`Invalid parts count: ${parts.length} for "${cleaned}"`);
			return null;
		}

		let [month, day, year] = parts.map((p) => parseInt(p, 10));
		console.log(`Parsed parts: month=${month}, day=${day}, year=${year}`);

		// Handle obvious OCR errors (swap month/day if month > 12)
		if (month > 12 && day <= 12) {
			[month, day] = [day, month];
			console.log(`Swapped month/day: month=${month}, day=${day}`);
		}

		// Handle 2-digit years
		if (year < 100) {
			year += year > 30 ? 1900 : 2000;
			console.log(`Adjusted year: ${year}`);
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
			console.log(
				`Validation failed: month=${month}, day=${day}, year=${year}`
			);
			return null;
		}

		const result = `${month.toString().padStart(2, "0")}/${day
			.toString()
			.padStart(2, "0")}/${year}`;
		console.log(`✅ Successfully normalized date: "${dateStr}" -> "${result}"`);
		return result;
	} catch (error) {
		console.warn("Date parsing error:", error, "for date:", dateStr);
		return null;
	}
}

/**
 * Check if a string is a valid date
 */
function isValidDate(dateStr: string): boolean {
	if (!dateStr || typeof dateStr !== "string") return false;
	return normalizeDate(dateStr) !== null;
}

/**
 * Check if a string is a valid name (not garbage)
 */
function isValidName(name: string): boolean {
	if (!name || typeof name !== "string") return false;
	return !isGarbageName(name);
}

/**
 * Combine adjacent entries where one has name and other has DOB
 * This handles the backend's stacked entry detection
 */
function combineStackedEntries(results: OCRResult[]): OCRResult[] {
	if (!results || results.length === 0) return results;

	const combined: OCRResult[] = [];
	let i = 0;

	while (i < results.length) {
		const current = results[i];
		const next = i + 1 < results.length ? results[i + 1] : null;

		// Simple combining logic - current has name, next has DOB
		if (
			next &&
			current.name &&
			current.name.trim() !== "" &&
			(!current.dob || current.dob.trim() === "") &&
			(!next.name || next.name.trim() === "") &&
			next.dob &&
			next.dob.trim() !== ""
		) {
			console.log(`🔗 Combining entries: "${current.name}" + "${next.dob}"`);
			combined.push({
				...current,
				dob: next.dob,
				score: Math.max(current.score || 0, next.score || 0),
			});
			i += 2; // Skip both entries
		} else {
			combined.push(current);
			i += 1;
		}
	}

	return combined;
}

/**
 * SIMPLIFIED normalization - minimal processing, let Fuse handle the fuzzy matching
 */
export function normalizeOCRResults(results: OCRResult[]): OCRResult[] {
	if (!results || results.length === 0) return results;

	console.log(
		"🔧 Starting SIMPLIFIED OCR normalization...",
		results.length,
		"results"
	);
	console.log("Raw input:", results);

	// Step 1: Combine stacked entries (name + DOB pairs)
	let normalized = combineStackedEntries(results);
	console.log(
		"📋 After combining stacked entries:",
		normalized.length,
		"results"
	);

	// Step 2: Minimal cleaning - just remove garbage and normalize dates
	normalized = normalized.map((result, index) => {
		console.log(`\n🔍 Processing entry ${index}:`, result);

		// Keep original name if it's not garbage, just trim whitespace
		const cleanName =
			result.name && !isGarbageName(result.name) ? result.name.trim() : "";

		// Normalize date if present
		const cleanDate = result.dob ? normalizeDate(result.dob) : null;

		console.log(`  Original: name="${result.name}", dob="${result.dob}"`);
		console.log(`  Cleaned: name="${cleanName}", dob="${cleanDate}"`);

		return {
			...result,
			name: cleanName,
			dob: cleanDate,
		};
	});

	// Step 3: Filter out completely empty entries
	const filtered = normalized.filter((result, index) => {
		const hasName = result.name && result.name.trim() !== "";
		const hasDate = result.dob && result.dob.trim() !== "";
		const shouldKeep = hasName || hasDate;

		console.log(`Filter ${index}:`, {
			result,
			hasName,
			hasDate,
			shouldKeep,
		});

		return shouldKeep;
	});

	console.log(
		"✅ SIMPLIFIED normalization complete:",
		filtered.length,
		"valid results"
	);
	console.log("Final filtered results:", filtered);
	return filtered;
}

// Export utility functions for testing
export { isValidName, isValidDate, combineStackedEntries };
