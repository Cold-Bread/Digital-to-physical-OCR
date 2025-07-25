// frontend/src/types/Patient.ts
export interface Patient {
	name: string;
	dob: string;
	last_visit: string;
	taken_from: string;
	placed_in: string;
	to_shred: boolean;
	date_shredded?: string; // optional
}
