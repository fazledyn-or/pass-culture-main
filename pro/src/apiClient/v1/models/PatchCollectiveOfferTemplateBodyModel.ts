/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CollectiveOfferVenueBodyModel } from './CollectiveOfferVenueBodyModel';
import type { DateRangeModel } from './DateRangeModel';
import type { EacFormat } from './EacFormat';
import type { StudentLevels } from './StudentLevels';
import type { SubcategoryIdEnum } from './SubcategoryIdEnum';

export type PatchCollectiveOfferTemplateBodyModel = {
  audioDisabilityCompliant?: boolean | null;
  bookingEmails?: Array<string> | null;
  contactEmail?: string | null;
  contactPhone?: string | null;
  dates?: DateRangeModel | null;
  description?: string | null;
  domains?: Array<number> | null;
  durationMinutes?: number | null;
  formats?: Array<EacFormat> | null;
  interventionArea?: Array<string> | null;
  mentalDisabilityCompliant?: boolean | null;
  motorDisabilityCompliant?: boolean | null;
  name?: string | null;
  nationalProgramId?: number | null;
  offerVenue?: CollectiveOfferVenueBodyModel | null;
  priceDetail?: string | null;
  students?: Array<StudentLevels> | null;
  subcategoryId?: SubcategoryIdEnum | null;
  venueId?: number | null;
  visualDisabilityCompliant?: boolean | null;
};

