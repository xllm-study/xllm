import s from "./SearchBar.module.scss";
import { SearchIcon } from "./SearchIcon";
export function SearchBar({
  query,
  setQuery,
}: {
  query: string;
  setQuery: (q: string) => void;
}) {
  return (
    <div className={s.searchBar}>
      <div className={s.icon}>
        <SearchIcon />
      </div>
      <input
        placeholder="search for a variable like smoking_history, etc."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
    </div>
  );
}
