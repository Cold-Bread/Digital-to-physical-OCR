import { create } from "zustand";
import { BackendResponse, BoxResponse, Patient, OCRResult, OCRGroup } from "../types/backendResponse";

type EditHistory = {
    patientList: BoxResponse;
    timestamp: number;
};

interface OCRStore {
    // OCR results from image processing
    ocrResponse: BackendResponse | null;
    allOCRResults: OCRResult[];        // All OCR results across all scans
    duplicateGroups: OCRGroup[];       // Groups of potential duplicates
    setOCRResponse: (resp: BackendResponse | null, imageSource: string) => void;
    addOCRResults: (results: OCRResult[], imageSource: string) => void;
    resolveDuplicate: (groupId: string, selectedId: string) => void;
    hasUnresolvedDuplicates: () => boolean;

    // Patient list response from box search
    patientList: BoxResponse;
    setPatientList: (list: BoxResponse) => void;
    updatePatient: (index: number, updatedPatient: Patient) => void;
    
    // Match tracking
    matchedResults: Map<number, OCRResult>; // patientIndex -> OCR result
    setMatch: (patientIndex: number, result: OCRResult) => void;
    removeMatch: (patientIndex: number) => void;
    
    // Box number management
    currentBoxNumber: string;
    setCurrentBoxNumber: (boxNumber: string) => void;
    applyBoxNumber: () => void;         // Apply current box number to matched patients

    // Edit history
    history: EditHistory[];
    addToHistory: (list: BoxResponse) => void;
    undo: () => void;
    undoAll: () => void;

    // Loading state
    isLoading: boolean;
    setIsLoading: (loading: boolean) => void;
    canProcessNewImage: () => boolean;  // Check if we can process a new image

    // Reset function for zero-state
    resetAll: () => void;
}

export const useOCRStore = create<OCRStore>((set, get) => ({
    // OCR state
    ocrResponse: null,
    allOCRResults: [],
    duplicateGroups: [],
    matchedResults: new Map(),
    currentBoxNumber: '',

    // Set OCR response and process for duplicates
    setOCRResponse: (resp, imageSource) => {
        console.log('Setting OCR Response:', resp);
        set({ ocrResponse: resp });
        if (resp) {
            get().addOCRResults(resp.ocr1, imageSource);
        }
    },

    // Add new OCR results and check for duplicates
    addOCRResults: (results, imageSource) => {
        const currentResults = [...get().allOCRResults];
        const newResults = results.map(result => ({
            ...result,
            id: Math.random().toString(36).substr(2, 9), // Generate unique ID
            imageSource,
            isPotentialDuplicate: false,
            isResolved: false
        }));

        // Check for duplicates
        const duplicateGroups: OCRGroup[] = [];
        const processedNames = new Set<string>();

        [...currentResults, ...newResults].forEach(result => {
            if (processedNames.has(result.name)) return;
            processedNames.add(result.name);

            const duplicates = [...currentResults, ...newResults].filter(r => 
                r.name.toLowerCase() === result.name.toLowerCase() &&
                (!r.dob || !result.dob || r.dob === result.dob)
            );

            if (duplicates.length > 1) {
                const groupId = Math.random().toString(36).substr(2, 9);
                duplicates.forEach(d => {
                    d.isPotentialDuplicate = true;
                    d.duplicateGroupId = groupId;
                });

                duplicateGroups.push({
                    id: groupId,
                    results: duplicates,
                    isResolved: false
                });
            }
        });

        set({
            allOCRResults: [...currentResults, ...newResults],
            duplicateGroups
        });
    },

    // Resolve a duplicate group
    resolveDuplicate: (groupId, selectedId) => {
        const currentResults = [...get().allOCRResults];
        const currentGroups = [...get().duplicateGroups];
        
        // Mark all results in the group as resolved
        currentResults.forEach(result => {
            if (result.duplicateGroupId === groupId) {
                result.isResolved = true;
                result.isPotentialDuplicate = result.id !== selectedId;
            }
        });

        // Mark the group as resolved
        const groupIndex = currentGroups.findIndex(g => g.id === groupId);
        if (groupIndex !== -1) {
            currentGroups[groupIndex].isResolved = true;
        }

        set({
            allOCRResults: currentResults,
            duplicateGroups: currentGroups
        });
    },

    // Check if there are any unresolved duplicates
    hasUnresolvedDuplicates: () => {
        return get().duplicateGroups.some(group => !group.isResolved);
    },

    // Match tracking
    setMatch: (patientIndex, result) => {
        const matches = new Map(get().matchedResults);
        matches.set(patientIndex, result);
        set({ matchedResults: matches });

        // Update the OCR result to mark it as matched
        const results = [...get().allOCRResults];
        const resultIndex = results.findIndex(r => r.id === result.id);
        if (resultIndex !== -1) {
            results[resultIndex] = { ...results[resultIndex], matchedPatientIndex: patientIndex };
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
            const resultIndex = results.findIndex(r => r.id === removedMatch.id);
            if (resultIndex !== -1) {
                results[resultIndex] = { ...results[resultIndex], matchedPatientIndex: undefined };
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
                    box_number: boxNumber
                };
            }
        });

        set({ patientList: currentList });
        get().addToHistory(currentList);
    },

    // Patient list management
    patientList: [],
    setPatientList: (list) => {
        console.log('Setting Patient List:', list);
        set({ patientList: list });
        get().addToHistory(list);
    },
    updatePatient: (index, updatedPatient) => {
        console.log('Updating Patient:', { index, updatedPatient });
        const currentList = [...get().patientList];
        currentList[index] = updatedPatient;
        set({ patientList: currentList });
        get().addToHistory(currentList);
    },

    // History management
    history: [],
    addToHistory: (list) => {
        console.log('Adding to history');
        const currentHistory = get().history;
        set({
            history: [...currentHistory, {
                patientList: JSON.parse(JSON.stringify(list)),
                timestamp: Date.now()
            }]
        });
    },
    undo: () => {
        console.log('Undoing last change');
        const currentHistory = get().history;
        if (currentHistory.length > 1) {
            const newHistory = [...currentHistory];
            newHistory.pop();
            const previousState = newHistory[newHistory.length - 1];
            set({
                patientList: previousState.patientList,
                history: newHistory
            });
        }
    },
    undoAll: () => {
        console.log('Undoing all changes');
        const currentHistory = get().history;
        if (currentHistory.length > 1) {
            const initialState = currentHistory[0];
            set({
                patientList: initialState.patientList,
                history: [initialState]
            });
        }
    },

    // Loading and validation
    isLoading: false,
    setIsLoading: (loading) => {
        console.log('Setting Loading State:', loading);
        set({ isLoading: loading });
    },

    canProcessNewImage: () => {
        return !get().hasUnresolvedDuplicates();
    },

    // Reset everything
    resetAll: () => {
        console.log('Resetting Store');
        set({
            ocrResponse: null,
            allOCRResults: [],
            duplicateGroups: [],
            matchedResults: new Map(),
            currentBoxNumber: '',
            patientList: [],
            isLoading: false,
            history: []
        });
    },
}));
