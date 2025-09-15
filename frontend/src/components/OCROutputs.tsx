import { Patient, OCRResult } from "../types/backendResponse";
import { useOCRStore } from "../store/useOCRStore";
import React, { useState } from "react";

interface OCROutputsProps {
    boxData: Patient[];
    selectedFile: File | null;
}

const OCROutputs = ({ boxData = [], selectedFile = null }: OCROutputsProps) => {
    const updatePatient = useOCRStore((s) => s.updatePatient);
    const allOCRResults = useOCRStore((s) => s.allOCRResults);
    const [editingCell, setEditingCell] = useState<{ index: number, field: keyof Patient } | null>(null);
    const [editValue, setEditValue] = useState("");
    
    // Debug log for store updates
    React.useEffect(() => {
        console.log('Store state changed:', {
            allOCRResults,
            resultCount: allOCRResults.length,
            boxDataCount: boxData.length
        });
    }, [allOCRResults, boxData]);
    
    // Filter out duplicate results that have been marked as duplicates and aren't selected
    const ocrData = React.useMemo(() => {
        const filtered = allOCRResults.filter(result => !result.isPotentialDuplicate || result.isResolved);
        console.log('Filtered OCR data:', {
            originalCount: allOCRResults.length,
            filteredCount: filtered.length,
            filtered
        });
        return filtered;
    }, [allOCRResults]);

    // Helper to normalize names for comparison
    const normalizeName = (name: string): string[] => {
        if (!name) return [];
        
        try {
            // First handle any OCR-specific patterns
            let normalized = String(name).toLowerCase()
                .replace(/d\.?o\.?b\.?/i, "")  // Remove "DOB" variations
                .replace(/[^\w\s.,]/g, "")     // Remove special characters except periods and commas
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
            
            variations.push(noSeparatorsVersion);

            // Process name parts
            const parts = spaceVersion.split(/[\s,]+/).filter(Boolean);
            if (parts.length >= 2) {
                const lastName = parts[parts.length - 1];
                const firstName = parts.slice(0, -1).join(" ");
                
                variations.push(
                    `${lastName}${firstName}`,
                    `${firstName}${lastName}`,
                    `${lastName} ${firstName}`,
                    `${firstName} ${lastName}`,
                    `${lastName},${firstName}`,
                    `${firstName},${lastName}`
                );
            } else {
                variations.push(spaceVersion);
            }
            
            return [...new Set(variations)]; // Remove duplicates
        } catch (error) {
            console.error("Error normalizing name:", error, { name });
            return [String(name).toLowerCase().trim()];
        }
    };

    // Helper to normalize date format
    const normalizeDate = (date: string): string => {
        try {
            if (!date) return "";
            
            // First remove any "D.O.B" or similar prefix and clean up the string
            const cleanDate = String(date)
                .replace(/d\.?o\.?b\.?/i, "")
                .replace(/[^\d\/\-]/g, "")
                .trim();
            
            // Try to extract numbers in the format MM/DD/YYYY or MM-DD-YYYY
            const dateMatch = cleanDate.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})$/);
            if (dateMatch) {
                let [, month, day, year] = dateMatch;
                month = month.padStart(2, '0');
                day = day.padStart(2, '0');
                if (year.length === 2) {
                    year = (parseInt(year) < 50 ? "20" : "19") + year;
                }
                return `${month}/${day}/${year}`;
            }
            
            // Try to extract 8 digits in a row (MMDDYYYY)
            const numbers = cleanDate.replace(/[^\d]/g, "");
            if (numbers.length === 8) {
                const month = numbers.substring(0, 2);
                const day = numbers.substring(2, 4);
                const year = numbers.substring(4, 8);
                return `${month}/${day}/${year}`;
            }
            
            return date; // Return original if we can't parse it
        } catch (error) {
            console.error("Error normalizing date:", error, { date });
            return String(date);
        }
    };

    type MatchResult = {
        isMatch: boolean;
        isPartialMatch: boolean;
        nameMatch: boolean;
        dobMatch: boolean;
    };

    // Helper to check match status between OCR result and box data
    const getMatchStatus = (ocrName: string, ocrDOB: string, boxName: string, boxDOB: string): MatchResult => {
        try {
            if (!ocrName || !boxName) return {
                isMatch: false,
                isPartialMatch: false,
                nameMatch: false,
                dobMatch: false
            };

            // Clean up DOB formats
            const cleanOcrDOB = ocrDOB?.replace(/d\.?o\.?b\.?[:, ]*/i, '').trim() || '';
            const cleanBoxDOB = boxDOB?.trim() || '';
            
            const normalizedOCRVariations = normalizeName(ocrName);
            const normalizedBoxVariations = normalizeName(boxName);
            const normalizedOCRDOB = normalizeDate(cleanOcrDOB);
            const normalizedBoxDOB = normalizeDate(cleanBoxDOB);

            // Check if any variation of the OCR name matches any variation of the box name
            const nameMatch = normalizedOCRVariations.some(ocrVar => 
                normalizedBoxVariations.some(boxVar => {
                    if (!ocrVar || !boxVar) return false;
                    // Direct match
                    if (ocrVar === boxVar) return true;
                    
                    // Remove any remaining special characters and spaces for comparison
                    const cleanOCR = ocrVar.replace(/[^a-z0-9]/g, "");
                    const cleanBox = boxVar.replace(/[^a-z0-9]/g, "");
                    
                    return cleanOCR === cleanBox;
                })
            );
            
            // Compare normalized dates
            const dobMatch = normalizedOCRDOB && normalizedBoxDOB && normalizedOCRDOB === normalizedBoxDOB;

            return {
                isMatch: nameMatch && dobMatch,
                isPartialMatch: nameMatch || dobMatch,
                nameMatch,
                dobMatch
            };
        } catch (error) {
            console.error("Error getting match status:", error, { ocrName, ocrDOB, boxName, boxDOB });
            return {
                isMatch: false,
                isPartialMatch: false,
                nameMatch: false,
                dobMatch: false
            };
        }
    };

    // Helper to check if a box patient has any matches in OCR results
    // Keep track of box row match status
    const [boxRowStatus] = useState<Map<number, string>>(new Map());

    const getBoxRowClass = (patient: Patient, index: number): string => {
        try {
            if (!patient || !patient.name || !patient.dob) return "row-no-match";
            
            // Check for existing match status
            if (boxRowStatus.has(index)) {
                return boxRowStatus.get(index) || "row-no-match";
            }
            
            const bestMatch = allOCRResults.reduce<MatchResult>(
                (best: MatchResult, ocr: OCRResult) => {
                    if (!ocr?.name || !ocr?.dob || ocr.isPotentialDuplicate) return best;
                    
                    const matchStatus = getMatchStatus(ocr.name, ocr.dob, patient.name, patient.dob);
                    if (matchStatus.isMatch) return matchStatus;
                    if (matchStatus.isPartialMatch && !best.isMatch) return matchStatus;
                    return best;
                },
                { isMatch: false, isPartialMatch: false, nameMatch: false, dobMatch: false }
            );

            // Store the match status
            const status = bestMatch.isMatch ? "row-match" : 
                          bestMatch.isPartialMatch ? "row-partial-match" : 
                          "row-no-match";
            boxRowStatus.set(index, status);
            
            return status;
        } catch (error) {
            console.error("Error getting box row class:", error, { patient });
            return "row-error";
        }
    };

    const handleEdit = (index: number, field: keyof Patient) => {
        setEditingCell({ index, field });
        setEditValue(String(boxData[index][field] || ""));
    };

    const handleSave = () => {
        if (!editingCell) return;
        
        try {
            const { index, field } = editingCell;
            const updatedPatient = { ...boxData[index] };

            // Type handling for different fields
            switch (field) {
                case 'is_child_when_joined':
                    updatedPatient.is_child_when_joined = editValue.toLowerCase() === 'true';
                    break;
                case 'year_joined':
                case 'last_dos':
                case 'shred_year':
                    const numValue = parseInt(editValue);
                    updatedPatient[field] = isNaN(numValue) ? 0 : numValue;
                    break;
                default:
                    updatedPatient[field] = editValue;
            }

            updatePatient(index, updatedPatient);
        } catch (error) {
            console.error("Error saving edit:", error);
        } finally {
            setEditingCell(null);
            setEditValue("");
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSave();
        } else if (e.key === 'Escape') {
            setEditingCell(null);
            setEditValue("");
        }
    };

    console.log('OCROutputs Props:', { boxData, allOCRResults });

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
                            <tr key={i} className={getBoxRowClass(patient, i)}>
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
                            <th>Confidence</th>
                            <th>Match Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(() => {
                            // If no OCR data, show placeholders
                            if (!ocrData || ocrData.length === 0) {
                                console.log('No OCR data available, showing empty rows');
                                return boxData.map((_, index) => (
                                    <tr key={`empty-${index}`} className="empty-row">
                                        <td colSpan={4}></td>
                                    </tr>
                                ));
                            }

                            // Show all OCR results
                            console.log('Rendering OCR results:', ocrData);
                            return ocrData.map((ocrResult, index) => {
                                if (!ocrResult?.name) return null;

                                // Try to find a match in box data
                                let bestMatchStatus: MatchResult | null = null;
                                for (const boxPatient of boxData) {
                                    if (!boxPatient?.name || !boxPatient?.dob) continue;

                                    const status = getMatchStatus(
                                        ocrResult.name,
                                        ocrResult.dob || '',
                                        boxPatient.name,
                                        boxPatient.dob
                                    );

                                    if (!bestMatchStatus || status.isMatch) {
                                        bestMatchStatus = status;
                                        if (status.isMatch) break;
                                    }
                                }

                                const rowClass = bestMatchStatus?.isMatch ? "row-match" : 
                                               bestMatchStatus?.isPartialMatch ? "row-partial-match" : 
                                               "row-no-match";

                                return (
                                    <tr key={`ocr-${index}`} className={rowClass}>
                                        <td>{ocrResult.name}</td>
                                        <td>{ocrResult.dob || 'N/A'}</td>
                                        <td>{ocrResult.score ? `${(ocrResult.score * 100).toFixed(1)}%` : 'N/A'}</td>
                                        <td>
                                            {bestMatchStatus ? (
                                                bestMatchStatus.isMatch ? "✓" : 
                                                bestMatchStatus.nameMatch ? "Name Match" : 
                                                bestMatchStatus.dobMatch ? "DOB Match" : "No Match"
                                            ) : "No Match"}
                                        </td>
                                    </tr>
                                );
                            }).filter((row): row is JSX.Element => row !== null);

                                // Debug logging for OCR data processing
                                console.log('Processing OCR data:', {
                                    ocrDataLength: ocrData.length,
                                    boxDataLength: boxData.length,
                                    ocrSample: ocrData.slice(0, 2)
                                });

                                // Display OCR results directly
                                return ocrData.map((ocrResult, ocrIndex) => {
                                    if (!ocrResult?.name) return null;

                                    // Find matching box record if any
                                    let bestBoxMatch = null;
                                    let bestMatchStatus = null;

                                    for (const boxPatient of boxData) {
                                        if (!boxPatient?.name || !boxPatient?.dob) continue;

                                        const status = getMatchStatus(
                                            String(ocrResult.name),
                                            String(ocrResult.dob || ''),
                                            String(boxPatient.name),
                                            String(boxPatient.dob)
                                        );

                                        if (status.isMatch || !bestBoxMatch) {
                                            bestBoxMatch = boxPatient;
                                            bestMatchStatus = status;
                                        }
                                    }

                                    const matchClass = bestMatchStatus?.isMatch ? "row-match" :
                                                     bestMatchStatus?.isPartialMatch ? "row-partial-match" :
                                                     "row-no-match";

                                    return (
                                        <tr key={`ocr-${ocrIndex}`} className={matchClass}>
                                            <td>{ocrResult.name}</td>
                                            <td>{ocrResult.dob || 'N/A'}</td>
                                            <td>{ocrResult.score ? `${(ocrResult.score * 100).toFixed(1)}%` : 'N/A'}</td>
                                            <td>
                                                {bestMatchStatus ? (
                                                    bestMatchStatus.isMatch ? "✓" :
                                                    bestMatchStatus.nameMatch ? "Name Match" :
                                                    bestMatchStatus.dobMatch ? "DOB Match" : "No Match"
                                                ) : "No Match"}
                                            </td>
                                        </tr>
                                    );
                                }).filter(Boolean);

                                // Create assignments map for exact matches first
                                const matchAssignments = new Map<number, number>();
                                const usedOCRIndices = new Set<number>();

                                // First pass: exact matches only
                                preComputedMatches.forEach(boxMatch => {
                                    if (!boxMatch) return;
                                    
                                    const exactMatch = boxMatch.matches.find(
                                        m => m.status.isMatch && !usedOCRIndices.has(m.ocrIndex)
                                    );

                                    if (exactMatch) {
                                        matchAssignments.set(boxMatch.boxIndex, exactMatch.ocrIndex);
                                        usedOCRIndices.add(exactMatch.ocrIndex);
                                    }
                                });

                                // Second pass: partial matches for remaining unmatched records
                                preComputedMatches.forEach(boxMatch => {
                                    if (!boxMatch || matchAssignments.has(boxMatch.boxIndex)) return;
                                    
                                    const partialMatch = boxMatch.matches.find(
                                        m => m.status.isPartialMatch && !usedOCRIndices.has(m.ocrIndex)
                                    );

                                    if (partialMatch) {
                                        matchAssignments.set(boxMatch.boxIndex, partialMatch.ocrIndex);
                                        usedOCRIndices.add(partialMatch.ocrIndex);
                                    }
                                });

                                // Track which OCR results have been used
                                const usedOCRResults = new Set<number>();

                                // Display all OCR results directly
                                console.log('Rendering OCR results:', ocrData);
                                
                                // Create rows for each box record
                                return boxData.map((boxPatient, boxIndex) => {
                                    // Find the best matching OCR result for this box row
                                    let bestMatch: OCRResult | null = null;
                                    let bestMatchStatus: ReturnType<typeof getMatchStatus> | null = null;

                                    // Only proceed if we have valid box data
                                    if (boxPatient?.name && boxPatient?.dob) {
                                        ocrData.forEach((ocr) => {
                                            if (!ocr?.name) return;
                                            
                                            const status = getMatchStatus(
                                                String(ocr.name),
                                                String(ocr.dob || ''),
                                                String(boxPatient.name),
                                                String(boxPatient.dob)
                                            );

                                            // If we find a match or if this is our first potential match
                                            if (status.isMatch || !bestMatch) {
                                                bestMatch = ocr;
                                            }
                                        });
                                    }

                                    // Only display OCR result if we have a decent match
                                    if (bestMatch) {
                                        const status = getMatchStatus(
                                            String(bestMatch.name),
                                            String(bestMatch.dob || ''),
                                            String(boxPatient.name),
                                            String(boxPatient.dob)
                                        );
                                        
                                        return (
                                            <tr key={`row-${boxIndex}`} className={status.isMatch ? "row-match" : "row-partial-match"}>
                                                <td>{bestMatch.name}</td>
                                                <td>{bestMatch.dob || 'N/A'}</td>
                                                <td>{bestMatch.score ? `${(bestMatch.score * 100).toFixed(1)}%` : 'N/A'}</td>
                                                <td>
                                                    {status.isMatch ? "✓" : 
                                                     status.nameMatch ? "Name Match" : 
                                                     status.dobMatch ? "DOB Match" : "No Match"}
                                                </td>
                                            </tr>
                                        );
                                    }

                                    // Show empty row if no match found
                                    return (
                                        <tr key={`empty-${boxIndex}`} className="empty-row">
                                            <td colSpan={4}></td>
                                        </tr>
                                    );
                                });
                            } catch (error) {
                                console.error("Error rendering OCR results:", error);
                                return (
                                    <tr className="row-error">
                                        <td colSpan={4}>Error processing OCR results</td>
                                    </tr>
                                );
                            }
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
