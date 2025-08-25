from nicegui import ui


def expired_contracts():
    
    with ui.element("div").classes("flex flex-col items-center justify-center max-w-6xl mt-8 mx-auto w-full"):
        ui.label("Expired Contract Agreement for:").classes("text-normal ml-4 font-bold ")
        ui.label("Acme corp.").classes("text-sm text-light ml-4 ")

    columns = [
        {
            "name": "id",
            "label": "Id",
            "field": "id",
            "align": "left",
        },
        {
            "name": "name",
            "label": "Name",
            "field": "name",
            "align": "left",
        },
        {
            "name": "contact",
            "label": "Contact Person",
            "field": "contact",
            "align": "left",
        },
        {
            "name": "country",
            "label": "Country",
            "field": "country",
            "align": "left",
        },
        {
            "name": "telephone",
            "label": "Telephone",
            "field": "telephone",
            "align": "left",
        },
        {
            "name": "email",
            "label": "Email",
            "field": "email",
            "align": "left",
        },
        {
            "name": "D.D. Performed",
            "label": "D.D. Performed",
            "field": "dd_performed",
            "align": "left",
        },
        {
            "name": "attention",
            "label": "Attention",
            "field": "attention",
            "align": "left",
        },
    ]
    columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }
    rows = [
        {
            "id": 1,
            "name": "Acme Corp",
            "contact": "John Doe",
            "country": "Aruba",
            "telephone": "+297 123 4567",
            "email": "john@acme.com",
            "dd_performed": "Yes",
            "attention": "None",
        },
        {
            "id": 2,
            "name": "Beta Ltd",
            "contact": "Jane Smith",
            "country": "USA",
            "telephone": "+1 555 234 5678",
            "email": "jane@beta.com",
            "dd_performed": "No",
            "attention": "Review",
        },
        {
            "id": 3,
            "name": "Gamma LLC",
            "contact": "Carlos Ruiz",
            "country": "Colombia",
            "telephone": "+57 321 654 9870",
            "email": "carlos@gamma.com",
            "dd_performed": "Yes",
            "attention": "Urgent",
        },
        {
            "id": 4,
            "name": "Delta Inc",
            "contact": "Anna Lee",
            "country": "Canada",
            "telephone": "+1 416 555 0192",
            "email": "anna@delta.com",
            "dd_performed": "No",
            "attention": "None",
        },
        {
            "id": 5,
            "name": "Epsilon GmbH",
            "contact": "Max Müller",
            "country": "Germany",
            "telephone": "+49 30 123456",
            "email": "max@epsilon.com",
            "dd_performed": "Yes",
            "attention": "Follow-up",
        },
        {
            "id": 6,
            "name": "Zeta S.A.",
            "contact": "Lucía Gómez",
            "country": "Spain",
            "telephone": "+34 912 345 678",
            "email": "lucia@zeta.com",
            "dd_performed": "No",
            "attention": "None",
        },
        {
            "id": 7,
            "name": "Eta Co.",
            "contact": "Tom Brown",
            "country": "UK",
            "telephone": "+44 20 7946 0958",
            "email": "tom@eta.com",
            "dd_performed": "Yes",
            "attention": "Review",
        },
        {
            "id": 8,
            "name": "Theta Pty",
            "contact": "Emily Clark",
            "country": "Australia",
            "telephone": "+61 2 9876 5432",
            "email": "emily@theta.com",
            "dd_performed": "No",
            "attention": "Urgent",
        },
        {
            "id": 9,
            "name": "Iota BV",
            "contact": "Pieter de Vries",
            "country": "Netherlands",
            "telephone": "+31 20 123 4567",
            "email": "pieter@iota.com",
            "dd_performed": "Yes",
            "attention": "None",
        },
        {
            "id": 10,
            "name": "Kappa SARL",
            "contact": "Sophie Dubois",
            "country": "France",
            "telephone": "+33 1 2345 6789",
            "email": "sophie@kappa.com",
            "dd_performed": "No",
            "attention": "Follow-up",
        },
    ]

    with ui.element("div").classes("max-w-6xl mt-12 mx-auto w-full"):
        ui.table(
            columns=columns, column_defaults=columns_defaults, rows=rows, pagination=3
        ).classes("w-full").props("flat").classes(
            "vendor-table shadow-lg rounded-lg overflow-hidden"
        )
        ui.add_css(".vendor-table thead tr { background-color: #144c8e !important; }")
