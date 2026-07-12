const roleStyles = {
  admin: "border-indigo-200 bg-indigo-50 text-indigo-700",
  pharmacist: "border-blue-200 bg-blue-50 text-blue-700",
  executive: "border-amber-200 bg-amber-50 text-amber-700"
};

export function RoleBadge({ role }) {
  return (
    <span className={`inline-flex h-8 items-center rounded-md border px-2.5 text-xs font-bold uppercase tracking-wide ${roleStyles[role] || roleStyles.pharmacist}`}>
      {role}
    </span>
  );
}

