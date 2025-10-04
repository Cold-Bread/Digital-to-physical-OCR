import { OCRResult } from "../types/backendResponse";

/**
 * ENHANCED OCR NORMALIZATION
 *
 * Improvements made to handle common OCR issues:
 *
 * 1. **Standalone DOB Detection**: Detects when a DOB appears alone and should be paired with previous name
 * 2. **Misclassified Date Handling**: Identifies dates that ended up in the name field and moves them to DOB
 * 3. **Mixed Text Extraction**: Extracts name and date from single OCR results containing both
 * 4. **Enhanced Date Patterns**: Better recognition of various date formats and OCR errors
 * 5. **Smart Name Validation**: Prevents dates from being classified as names
 * 6. **Improved Stacking Logic**: Multiple strategies for combining related OCR entries
 *
 * The normalization now handles these common scenarios:
 * - "John Smith" followed by "12/25/1990" → combines into single entry
 * - "John Smith 12/25/1990" → extracts into separate name and DOB
 * - Name field containing "12/25/1990" → moves to DOB field
 * - Better DOB prefix detection (DOB:, DATE OF BIRTH:, etc.)
 */

// Date format patterns - enhanced for better OCR date detection
const DATE_PATTERNS = [
	/^\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{2,4}$/, // MM/DD/YYYY, MM-DD-YY, etc.
	/^(DOB|SOB|OOB|D0B|D08)[-:]?\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{2,4}$/i, // DOB:MM/DD/YYYY
	/^\d{1,2}[,]\d{1,2}[-]\d{1,2}[-]\d{2,4}$/, // Mixed separators like "13,6-29-77"
	/^\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{1,4}$/, // Flexible pattern for OCR errors
	/^\d{1,2}[\/\-,]\d{1,2}$/, // MM/DD or MM-DD (missing year)
	/^\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{1,2}$/, // MM/DD/YY with single digit year
];

// Enhanced patterns to detect dates that might be misclassified as names
const LIKELY_DATE_PATTERNS = [
	/\b\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{2,4}\b/, // Date anywhere in string
	/\b(DOB|D\.O\.B\.?|DATE OF BIRTH)[-:\s]*\d/i, // DOB prefix patterns
	/^\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{2,4}/, // Starts with date
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

	// Check if it's actually a date disguised as a name
	if (isValidDate(trimmed)) return true;

	// Check for obvious date patterns even if they don't pass full validation
	if (/^\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{1,4}$/.test(trimmed)) return true;

	return false;
}

/**
 * Basic date normalization - handle OCR prefixes and format
 */
function normalizeDate(dateStr: string): string | null {
	if (!dateStr || typeof dateStr !== "string") return null;

	let cleaned = dateStr.trim();
	console.log(`🗓️ Normalizing date: "${dateStr}" -> cleaned: "${cleaned}"`);

	// Remove ALL variations of DOB prefixes (comprehensive OCR error handling)
	cleaned = cleaned.replace(
		/^(DOB|SOB|OOB|D0B|D08|DOE|D0E|DOG|D0G|BOB|B0B|BOD|B0D|DATE OF BIRTH|BIRTH DATE|BIRTHDAY)[-:\s]*/i,
		""
	);

	// Handle DOB that might appear anywhere in the string, not just at start
	cleaned = cleaned.replace(
		/(DOB|SOB|OOB|D0B|D08|DOE|D0E|DOG|D0G|BOB|B0B|BOD|B0D)[-:\s]+/gi,
		""
	);

	// Remove common OCR suffixes and cleanup
	cleaned = cleaned.replace(/[,.]*$/, ""); // Remove trailing punctuation
	cleaned = cleaned.replace(/^[:\-\s]+/, ""); // Remove leading separators

	console.log(`After comprehensive DOB prefix/suffix removal: "${cleaned}"`);

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
 * Check if a string looks like it contains a date (even if mixed with other text)
 */
function containsLikelyDate(text: string): boolean {
	if (!text || typeof text !== "string") return false;
	return LIKELY_DATE_PATTERNS.some((pattern) => pattern.test(text.trim()));
}

/**
 * Extract date from text that contains both name and date
 */
function extractDateFromMixedText(
	text: string
): { name: string; date: string } | null {
	if (!text || typeof text !== "string") return null;

	const trimmed = text.trim();

	// Look for DOB prefix patterns (most explicit)
	const dobMatch = trimmed.match(
		/^(.+?)\s+(DOB|D\.O\.B\.?|DATE OF BIRTH|BIRTH DATE)[-:\s]*(.+)$/i
	);
	if (dobMatch && dobMatch[1].trim() && dobMatch[3].trim()) {
		return {
			name: dobMatch[1].trim(),
			date: dobMatch[3].trim(),
		};
	}

	// Look for dates at the end with various separators
	const dateAtEndMatch = trimmed.match(
		/^(.+?)\s+(\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{1,4})$/
	);
	if (
		dateAtEndMatch &&
		dateAtEndMatch[1].trim() &&
		!isGarbageName(dateAtEndMatch[1].trim())
	) {
		return {
			name: dateAtEndMatch[1].trim(),
			date: dateAtEndMatch[2].trim(),
		};
	}

	// Look for dates at the beginning
	const dateAtStartMatch = trimmed.match(
		/^(\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{1,4})\s+(.+)$/
	);
	if (
		dateAtStartMatch &&
		dateAtStartMatch[2].trim() &&
		!isGarbageName(dateAtStartMatch[2].trim())
	) {
		return {
			name: dateAtStartMatch[2].trim(),
			date: dateAtStartMatch[1].trim(),
		};
	}

	// Look for comma-separated name and date
	const commaSeparatedMatch = trimmed.match(
		/^([^,]+),\s*(\d{1,2}[\/\-,]\d{1,2}[\/\-,]\d{1,4})$/
	);
	if (
		commaSeparatedMatch &&
		commaSeparatedMatch[1].trim() &&
		!isGarbageName(commaSeparatedMatch[1].trim())
	) {
		return {
			name: commaSeparatedMatch[1].trim(),
			date: commaSeparatedMatch[2].trim(),
		};
	}

	return null;
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
 * Enhanced logic to handle more OCR scenarios
 */
function combineStackedEntries(results: OCRResult[]): OCRResult[] {
	if (!results || results.length === 0) return results;

	const combined: OCRResult[] = [];
	let i = 0;

	while (i < results.length) {
		const current = results[i];
		const next = i + 1 < results.length ? results[i + 1] : null;

		console.log(`🔍 Processing entry ${i}:`, current);
		console.log(`🔍 Next entry ${i + 1}:`, next);

		// Case 1: Current has name, next has only DOB (original logic)
		if (
			next &&
			current.name &&
			current.name.trim() !== "" &&
			(!current.dob || current.dob.trim() === "") &&
			(!next.name || next.name.trim() === "") &&
			next.dob &&
			next.dob.trim() !== ""
		) {
			console.log(
				`🔗 Case 1 - Combining name + DOB: "${current.name}" + "${next.dob}"`
			);
			combined.push({
				...current,
				dob: next.dob,
				score: Math.max(current.score || 0, next.score || 0),
			});
			i += 2; // Skip both entries
			continue;
		}

		// Case 2: Next entry has a name that looks like a standalone date
		if (
			next &&
			current.name &&
			current.name.trim() !== "" &&
			(!current.dob || current.dob.trim() === "") &&
			next.name &&
			isValidDate(next.name) && // Next "name" is actually a date
			(!next.dob || next.dob.trim() === "")
		) {
			console.log(
				`🔗 Case 2 - Name + misclassified date: "${current.name}" + "${next.name}"`
			);
			combined.push({
				...current,
				dob: normalizeDate(next.name),
				score: Math.max(current.score || 0, next.score || 0),
			});
			i += 2; // Skip both entries
			continue;
		}

		// Case 3: Current entry has mixed name+date in one field
		if (current.name && containsLikelyDate(current.name)) {
			const extracted = extractDateFromMixedText(current.name);
			if (extracted) {
				console.log(
					`🔗 Case 3 - Extracting from mixed text: "${current.name}" -> name: "${extracted.name}", date: "${extracted.date}"`
				);
				combined.push({
					...current,
					name: extracted.name,
					dob: normalizeDate(extracted.date),
				});
				i += 1;
				continue;
			}
		}

		// Case 4: Current name field contains a date that should be moved to DOB
		if (
			current.name &&
			current.name.trim() !== "" &&
			isValidDate(current.name) &&
			(!current.dob || current.dob.trim() === "")
		) {
			console.log(
				`🔗 Case 4 - Moving date from name to DOB: "${current.name}"`
			);
			combined.push({
				...current,
				name: "", // Clear name since it was actually a date
				dob: normalizeDate(current.name),
			});
			i += 1;
			continue;
		}

		// Default: No special processing needed
		combined.push(current);
		i += 1;
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

	// Step 2: Clean all DOB fields after stacking to ensure comprehensive prefix removal
	normalized = normalized.map((result, index) => {
		console.log(`\n🧹 Post-stacking DOB cleanup for entry ${index}:`, result);

		// Clean DOB field if it exists (this catches DOBs that were just combined/moved)
		let cleanedDOB = result.dob;
		if (cleanedDOB && cleanedDOB.trim() !== "") {
			const originalDOB = cleanedDOB;
			cleanedDOB = normalizeDate(cleanedDOB);
			console.log(`  🗓️ DOB cleanup: "${originalDOB}" → "${cleanedDOB}"`);
		}

		return {
			...result,
			dob: cleanedDOB,
		};
	});

	console.log(
		"🧽 After post-stacking DOB cleanup:",
		normalized.length,
		"results"
	);

	// Step 3: Enhanced cleaning with better date/name detection
	normalized = normalized.map((result, index) => {
		console.log(`\n🔍 Final processing entry ${index}:`, result);

		let cleanName = "";
		let cleanDate: string | null = null;

		// Handle name field
		if (result.name && result.name.trim() !== "") {
			const trimmedName = result.name.trim();

			// Check if name field actually contains a date
			if (isValidDate(trimmedName)) {
				console.log(`  📅 Name field contains date: "${trimmedName}"`);
				cleanDate = normalizeDate(trimmedName);
			}
			// Check if name contains mixed name+date
			else if (containsLikelyDate(trimmedName)) {
				const extracted = extractDateFromMixedText(trimmedName);
				if (extracted) {
					console.log(
						`  🔀 Extracted from name: name="${extracted.name}", date="${extracted.date}"`
					);
					cleanName = extracted.name;
					cleanDate = normalizeDate(extracted.date);
				} else if (!isGarbageName(trimmedName)) {
					cleanName = trimmedName;
				}
			}
			// Regular name processing
			else if (!isGarbageName(trimmedName)) {
				cleanName = trimmedName;
			}
		}

		// Handle DOB field (only if we haven't already found a date)
		if (!cleanDate && result.dob && result.dob.trim() !== "") {
			cleanDate = normalizeDate(result.dob);
		}

		console.log(`  Original: name="${result.name}", dob="${result.dob}"`);
		console.log(`  Enhanced: name="${cleanName}", dob="${cleanDate}"`);

		return {
			...result,
			name: cleanName,
			dob: cleanDate,
		};
	});

	// Step 4: Filter out completely empty entries
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
export {
	isValidName,
	isValidDate,
	combineStackedEntries,
	containsLikelyDate,
	extractDateFromMixedText,
};
