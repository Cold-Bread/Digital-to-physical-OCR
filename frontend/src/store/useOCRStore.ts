import { create } from "zustand";
import { BackendResponse, BoxResponse, Patient } from "../types/backendResponse";

type EditHistory = {
    patientList: BoxResponse;
    timestamp: number;
};

interface OCRStore {
    // OCR results from image processing
    ocrResponse: BackendResponse | null;
    setOCRResponse: (resp: BackendResponse | null) => void;

    // Patient list response from box search
    patientList: BoxResponse;
    setPatientList: (list: BoxResponse) => void;
    updatePatient: (index: number, updatedPatient: Patient) => void;

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

export const useOCRStore = create<OCRStore>((set, get) => ({
    ocrResponse: null,
    setOCRResponse: (resp) => {
        console.log('Setting OCR Response:', resp);
        set({ ocrResponse: resp });
    },

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
            newHistory.pop(); // Remove current state
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

    isLoading: false,
    setIsLoading: (loading) => {
        console.log('Setting Loading State:', loading);
        set({ isLoading: loading });
    },

    resetAll: () => {
        console.log('Resetting Store');
        set({
            ocrResponse: null,
            patientList: [],
            isLoading: false,
            history: []
        });
    },
}));
