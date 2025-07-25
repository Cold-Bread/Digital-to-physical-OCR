// frontend/src/store/patientStore.ts
import { Patient } from "../types/patient";
import { create } from "zustand";

interface PatientState {
	currentPatient: Patient;
	ocrOutput: Patient;
	editableText: Patient;
	setPatient: (patient: Patient) => void;
	setOcrOutput: (ocr: Patient) => void;
	setEditableText: (text: Patient) => void;
	resetEditableText: () => void;
}

export const usePatientStore = create<PatientState>((set, get) => ({
	currentPatient: {
		name: "",
		dob: "",
		last_visit: "",
		taken_from: "",
		placed_in: "",
		to_shred: false,
		date_shredded: "",
	},
	ocrOutput: {
		name: "",
		dob: "",
		last_visit: "",
		taken_from: "",
		placed_in: "",
		to_shred: false,
		date_shredded: "",
	},
	editableText: {
		name: "",
		dob: "",
		last_visit: "",
		taken_from: "",
		placed_in: "",
		to_shred: false,
		date_shredded: "",
	},
	setPatient: (patient) => set({ currentPatient: patient }),
	setOcrOutput: (ocr) => set({ ocrOutput: ocr }),
	setEditableText: (text) => set({ editableText: text }),
	resetEditableText: () => set({ editableText: get().ocrOutput }),
}));
