import { Patient, OCRResult } from "../types/backendResponse";
import { useOCRStore } from "../store/useOCRStore";
import { useState } from "react";

interface OCROutputsProps {
    boxData: Patient[];
    ocrData: OCRResult[];
    selectedFile: File | null;
}

const OCROutputs = ({ boxData = [], ocrData = [], selectedFile = null }: OCROutputsProps) => {
    const updatePatient = useOCRStore((s) => s.updatePatient);
    const undo = useOCRStore((s) => s.undo);
    const undoAll = useOCRStore((s) => s.undoAll);
    const [editingCell, setEditingCell] = useState<{ index: number, field: keyof Patient } | null>(null);
    const [editValue, setEditValue] = useState("");

    console.log('OCROutputs Render:', {
        boxDataLength: boxData.length,
        ocrDataLength: ocrData.length,
        boxDataSample: boxData[0],
        ocrDataSample: ocrData[0],
        editingCell
    });

    // Helper to normalize names for comparison
    const normalizeName = (name: string): string[] => {
        // First handle any OCR-specific patterns
        let normalized = name.toLowerCase()
            .replace(/d\.?o\.?b\.?/i, "")  // Remove "DOB" variations
            .trim();
            
        // Create variations with different separator handling
        const variations: string[] = [];
        
        // Version 1: Convert all separators to spaces
        const spaceVersion = normalized
            .replace(/[.,;:\-_]/g, " ")
            .replace(/\s+/g, " ")
            .trim();
            
        // Version 2: Remove all separators
        const noSeparatorsVersion = normalized
            .replace(/[.,;:\-_\s]/g, "")
            .trim();
            
        // Version 3: Keep periods but normalize other separators
        const periodVersion = normalized
            .replace(/[,;:\-_]/g, " ")  // Convert other separators to spaces
            .replace(/\s+/g, " ")       // Normalize spaces
            .trim();

        // Add base versions to variations
        variations.push(noSeparatorsVersion);

        // Process each version for name order variations
        [spaceVersion, periodVersion].forEach(version => {
            const parts = version.split(",").map(part => part.trim());
            let firstName, lastName;
            
            if (parts.length === 2) {
                // Already in "Last, First" format
                [lastName, firstName] = parts;
            } else {
                // Handle "First Last" format
                const words = parts[0].split(/[\s.]+/); // Split on spaces or periods
                if (words.length >= 2) {
                    lastName = words.pop() || "";
                    firstName = words.join(" ");
                } else {
                    variations.push(parts[0]);
                    return;
                }
            }
            
            // Create all possible combinations
            const names = [
                `${lastName}${firstName}`,         // No spaces
                `${firstName}${lastName}`,         // No spaces alternate
                `${lastName} ${firstName}`,        // With space
                `${firstName} ${lastName}`,        // With space alternate
                `${lastName}.${firstName}`,        // With period
                `${firstName}.${lastName}`,        // With period alternate
                lastName + firstName.replace(/\s+/g, "."),  // Period between all parts
                firstName.replace(/\s+/g, ".") + lastName,  // Period between all parts alternate
            ];
            
            variations.push(...names);
        });
        
        return variations;
    };

    // Helper to normalize date format
    const normalizeDate = (date: string) => {
        // First remove any "D.O.B" or similar prefix
        const cleanDate = date.replace(/d\.?o\.?b\.?/i, "").trim();
        
        // Remove any non-numeric characters but keep track of where numbers were
        const numbers = cleanDate.replace(/[^0-9]/g, "");
        
        // Handle different formats
        if (numbers.length === 8) {
            // Full format: MMDDYYYY
            const month = numbers.substring(0, 2);
            const day = numbers.substring(2, 4);
            const year = numbers.substring(4, 8);
            return `${month}/${day}/${year}`;
        } else if (numbers.length === 6) {
            // Short year format: MMDDYY
            const month = numbers.substring(0, 2);
            const day = numbers.substring(2, 4);
            let year = numbers.substring(4, 6);
            // Convert 2-digit year to 4-digit
            const fullYear = parseInt(year) < 50 ? "20" + year : "19" + year;
            return `${month}/${day}/${fullYear}`;
        }
        
        // If we can't parse it, try to match it against known formats
        const dateMatch = cleanDate.match(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})/);
        if (dateMatch) {
            let [, month, day, year] = dateMatch;
            // Pad month and day with leading zeros if needed
            month = month.padStart(2, '0');
            day = day.padStart(2, '0');
            // Convert 2-digit year to 4-digit
            if (year.length === 2) {
                year = (parseInt(year) < 50 ? "20" : "19") + year;
            }
            return `${month}/${day}/${year}`;
        }
        
        return date; // Return original if we can't parse it
    };

type MatchResult = {
    isMatch: boolean;
    isPartialMatch: boolean;
    nameMatch: boolean;
    dobMatch: boolean;
};

type MatchWithIndex = {
    index: number;
    status: MatchResult;
};

// Helper to check match status between OCR result and box data
    const getMatchStatus = (ocrName: string, ocrDOB: string, boxName: string, boxDOB: string): MatchResult => {
        const normalizedOCRVariations = normalizeName(ocrName);
        const normalizedBoxVariations = normalizeName(boxName);
        const normalizedOCRDOB = normalizeDate(ocrDOB);
        const normalizedBoxDOB = normalizeDate(boxDOB);

        // Check if any variation of the OCR name matches any variation of the box name
        const nameMatch = normalizedOCRVariations.some(ocrVar => 
            normalizedBoxVariations.some(boxVar => {
                // Direct match
                if (ocrVar === boxVar) return true;
                
                // Remove any remaining special characters and spaces for comparison
                const cleanOCR = ocrVar.replace(/[^a-z0-9]/g, "");
                const cleanBox = boxVar.replace(/[^a-z0-9]/g, "");
                
                return cleanOCR === cleanBox;
            })
        );
        
        // Compare normalized dates
        const dobMatch = normalizedOCRDOB === normalizedBoxDOB;

        return {
            isMatch: nameMatch && dobMatch,
            isPartialMatch: nameMatch || dobMatch,
            nameMatch,
            dobMatch
        };
    };

    // Helper to check if a box patient has any matches in OCR results
    const getBoxRowClass = (patient: Patient): string => {
        const bestMatch = ocrData.reduce<MatchResult>(
            (best, ocr) => {
                const matchStatus = getMatchStatus(ocr.name, ocr.dob, patient.name, patient.dob);
                if (matchStatus.isMatch) return matchStatus;
                if (matchStatus.isPartialMatch && !best.isMatch) return matchStatus;
                return best;
            },
            { isMatch: false, isPartialMatch: false, nameMatch: false, dobMatch: false }
        );

        if (bestMatch.isMatch) return "row-match";
        if (bestMatch.isPartialMatch) return "row-partial-match";
        return "row-no-match";
    };

    const handleEdit = (index: number, field: keyof Patient) => {
        setEditingCell({ index, field });
        setEditValue(String(boxData[index][field]));
    };

    const handleSave = () => {
        if (!editingCell) return;
        
        const { index, field } = editingCell;
        const updatedPatient = { ...boxData[index] };

        // Type handling for different fields
        switch (field) {
            case 'is_child_when_joined':
                updatedPatient.is_child_when_joined = editValue.toLowerCase() === 'true';
                break;
            case 'year_joined':
                updatedPatient.year_joined = parseInt(editValue) || 0;
                break;
            case 'last_dos':
                updatedPatient.last_dos = parseInt(editValue) || 0;
                break;
            case 'shred_year':
                updatedPatient.shred_year = parseInt(editValue) || 0;
                break;
            case 'name':
                updatedPatient.name = editValue;
                break;
            case 'dob':
                updatedPatient.dob = editValue;
                break;
            case 'box_number':
                updatedPatient.box_number = editValue;
                break;
        }

        updatePatient(index, updatedPatient);
        setEditingCell(null);
        setEditValue("");
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSave();
        } else if (e.key === 'Escape') {
            setEditingCell(null);
            setEditValue("");
        }
    };



    return (
        <div className="outputs-container">
            <div className="main-table-container">
                <h3>Box Records</h3>
                <table className="main-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>DOB</th>
                            <th>Year Joined</th>
                            <th>Last DOS</th>
                            <th>Shred Year</th>
                            <th>Child When Joined</th>
                            <th>Box Number</th>
                        </tr>
                    </thead>
                    <tbody>
                        {boxData.map((patient, i) => (
                            <tr key={i} className={getBoxRowClass(patient)}>
                                {(Object.keys(patient) as Array<keyof Patient>).map((field) => (
                                    <td 
                                        key={field} 
                                        onClick={() => handleEdit(i, field)}
                                        className={editingCell?.index === i && editingCell?.field === field ? "editing" : ""}
                                    >
                                        {editingCell?.index === i && editingCell?.field === field ? (
                                            <input
                                                type={field === 'is_child_when_joined' ? 'checkbox' : 'text'}
                                                value={editValue}
                                                onChange={(e) => setEditValue(field === 'is_child_when_joined' ? e.target.checked.toString() : e.target.value)}
                                                onKeyDown={handleKeyDown}
                                                onBlur={handleSave}
                                                autoFocus
                                            />
                                        ) : (
                                            field === 'is_child_when_joined' ? 
                                                (patient[field] ? "Yes" : "No") : 
                                                patient[field]
                                        )}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="side-table-container">
                <h3>OCR Results</h3>
                <table className="side-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>DOB</th>
                            <th>Match Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(() => {
                            // Track which OCR results have been matched
                            const matchedOCRIndices = new Set<number>();
                            
                            // First pass: Show matches for box data
                            return [...boxData.map((boxPatient, boxIndex) => {
                                // Find best matching OCR result for this box record
                                let bestMatch: MatchWithIndex | null = null;
                                
                                ocrData.forEach((ocrResult, ocrIndex) => {
                                    if (matchedOCRIndices.has(ocrIndex)) return; // Skip if already matched
                                    
                                    const matchStatus = getMatchStatus(
                                        ocrResult.name,
                                        ocrResult.dob,
                                        boxPatient.name,
                                        boxPatient.dob
                                    );
                                    
                                    if (matchStatus.isMatch || 
                                        (matchStatus.isPartialMatch && (!bestMatch || !bestMatch.status.isMatch))) {
                                        bestMatch = { index: ocrIndex, status: matchStatus };
                                    }
                                });

                                try {
                                    if (bestMatch && typeof bestMatch === 'object') {
                                        const match = bestMatch as MatchWithIndex;
                                        // Mark this OCR result as matched
                                        matchedOCRIndices.add(match.index);
                                        const matchingOCR = ocrData[match.index];
                                        const rowClass = match.status.isMatch ? "row-match" : "row-partial-match";

                                        return (
                                            <tr key={`match-${boxIndex}`} className={rowClass}>
                                                <td>{matchingOCR.name}</td>
                                                <td>{matchingOCR.dob}</td>
                                                <td>
                                                    {match.status.isMatch ? "✓" : 
                                                     match.status.nameMatch ? "Name Match" : "DOB Match"}
                                                </td>
                                            </tr>
                                        );
                                    } else {
                                        // No match found for this box record
                                        return (
                                            <tr key={`empty-${boxIndex}`} className="empty-row">
                                                <td colSpan={3}></td>
                                            </tr>
                                        );
                                    }
                                } catch (error) {
                                    console.error("Error processing match:", error, bestMatch);
                                    // Return an error row in case of error
                                    return (
                                        <tr key={`error-${boxIndex}`} className="row-error">
                                            <td colSpan={3}>Error processing match</td>
                                        </tr>
                                    );
                                }
                            }),
                            // Second pass: Show remaining unmatched OCR results
                            ...ocrData.map((ocrResult, index) => {
                                if (!matchedOCRIndices.has(index)) {
                                    return (
                                        <tr key={`unmatched-${index}`} className="row-no-match">
                                            <td>{ocrResult.name}</td>
                                            <td>{ocrResult.dob}</td>
                                            <td>No Match</td>
                                        </tr>
                                    );
                                }
                                return null;
                            }).filter(Boolean)]
                        })()}
                    </tbody>
                </table>
            </div>
            {selectedFile && (
                <div className="image-preview-container">
                    <h3>Original Image</h3>
                    <img
                        src={URL.createObjectURL(selectedFile)}
                        alt="Original document"
                        className="image-preview"
                    />
                </div>
            )}
        </div>
    );
};

export default OCROutputs;
