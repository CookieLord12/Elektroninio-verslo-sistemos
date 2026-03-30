# Testing checklist

## Functional tests

| ID | Test case | Expected result | Result | Status |
|---|---|---|---|---|
| T1 | Homepage opens | Homepage loads without PHP/database errors | Homepage opens correctly | Passed |
| T2 | Category page opens | Category grid shows products with image, title and price | Category listing works | Passed |
| T3 | Product page opens | Product page shows description, price, category and image | Product detail page works | Passed |
| T4 | Product import | All 20 products imported successfully | 20 products visible in catalog | Passed |
| T5 | Product images | Every product has at least one image | All product cards show images | Passed |
| T6 | Navigation | User can move between categories and products easily | Main navigation works | Passed |
| T7 | Search | Search returns matching product names | Search finds relevant products | Passed |
| T8 | Review form | User can submit product review | Review modal/form works | Passed |
| T9 | Review display | Approved review appears on product page | Review visible after approval | Passed |
| T10 | Mobile layout | Layout adapts on narrow screen | Responsive layout works | Passed |

## Problems identified and resolved

1. **Image import paths** - PrestaShop imports images more reliably from absolute URLs, so a static image server on port 8081 was added and `prepare_import.py` generates the final CSV.
2. **Theme consistency** - a jewelry-specific palette and consistent product naming were applied to avoid the generic look of raw generated fixtures.
3. **Review moderation** - optional moderation was enabled to prevent inappropriate comments during testing.

## Optimization ideas

- Compress generated images if page speed becomes an issue.
- Enable caching and friendly URLs.
- Add product tags and related products for better catalog exploration.
