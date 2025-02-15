/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DMSApplicationForEAC } from './DMSApplicationForEAC';
import type { VenueTypeCode } from './VenueTypeCode';

export type GetOffererVenueResponseModel = {
  adageInscriptionDate?: string | null;
  address?: string | null;
  audioDisabilityCompliant?: boolean | null;
  bannerMeta?: Record<string, any> | null;
  bannerUrl?: string | null;
  bookingEmail?: string | null;
  city?: string | null;
  collectiveDmsApplications: Array<DMSApplicationForEAC>;
  comment?: string | null;
  demarchesSimplifieesApplicationId?: number | null;
  departementCode?: string | null;
  hasAdageId: boolean;
  hasCreatedOffer: boolean;
  hasMissingReimbursementPoint: boolean;
  hasPendingBankInformationApplication?: boolean | null;
  hasVenueProviders: boolean;
  id: number;
  isPermanent: boolean;
  isVirtual: boolean;
  mentalDisabilityCompliant?: boolean | null;
  motorDisabilityCompliant?: boolean | null;
  name: string;
  postalCode?: string | null;
  publicName?: string | null;
  siret?: string | null;
  venueTypeCode: VenueTypeCode;
  visualDisabilityCompliant?: boolean | null;
  withdrawalDetails?: string | null;
};

