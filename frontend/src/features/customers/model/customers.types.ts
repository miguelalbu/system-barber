/** Client domain types, mirroring the backend contract (`ClientOut`, `ClientPage`). */

export interface Client {
  id: string;
  name: string;
  /** E.164, e.g. "+5511987654321". */
  phone: string;
  email: string | null;
  /** "YYYY-MM-DD". */
  birth_date: string | null;
  notes: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientInput {
  name: string;
  phone: string;
  email: string | null;
  birth_date: string | null;
  notes: string | null;
  active: boolean;
}

export interface ClientPage {
  items: Client[];
  /** Matches across every page. */
  total: number;
}

export interface ClientQuery {
  q: string;
  page: number;
}
