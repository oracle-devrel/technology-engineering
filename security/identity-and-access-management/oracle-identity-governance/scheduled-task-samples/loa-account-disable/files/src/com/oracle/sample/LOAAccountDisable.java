/*******************************************************************************
 * Copyright (c) 2025 Oracle and/or its affiliates. All rights reserved. DO NOT
 * ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
 *
 * The Universal Permissive License (UPL), Version 1.0
 *
 * Subject to the condition set forth below, permission is hereby granted to any
 * person obtaining a copy of this software, associated documentation and/or
 * data (collectively the "Software"), free of charge and under any and all
 * copyright rights in the Software, and any and all patent rights owned or
 * freely licensable by each licensor hereunder covering either (i) the
 * unmodified Software as contributed to or provided by such licensor, or (ii)
 * the Larger Works (as defined below), to deal in both
 *
 * (a) the Software, and
 *
 * (b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
 * one is included with the Software each a "Larger Work" to which the Software
 * is contributed by such licensors),
 *
 * without restriction, including without limitation the rights to copy, create
 * derivative works of, display, perform, and distribute the Software and make,
 * use, sell, offer for sale, import, export, have made, and have sold the
 * Software and the Larger Work(s), and to sublicense the foregoing rights on
 * either these or other terms.
 *
 * This license is subject to the following condition:
 *
 * The above copyright notice and either this complete permission notice or at a
 * minimum a reference to the UPL must be included in all copies or substantial
 * portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *******************************************************************************/

package com.oracle.sample;

import java.util.Calendar;

import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

import oracle.iam.identity.usermgmt.api.UserManager;
import oracle.iam.identity.usermgmt.api.UserManagerConstants;
import oracle.iam.identity.usermgmt.vo.User;
import oracle.iam.platform.Platform;
import oracle.iam.platform.entitymgr.vo.SearchCriteria;
import oracle.iam.provisioning.api.ProvisioningConstants;
import oracle.iam.provisioning.api.ProvisioningService;
import oracle.iam.provisioning.vo.Account;
import oracle.iam.scheduler.exception.SchedulerException;
import oracle.iam.scheduler.vo.TaskSupport;

/**
 * Sample scheduled task implementation that disables all the access of a user
 * which goes on a leave of absence. The LOA status is determined based on a
 * custom attribute (UDF), specified as a parameter in the scheduled task
 * definition.
 * 
 * The scheduled task will also handle the re-enabling of user accounts once the
 * LOA end date is hit, and also the clearing of the UDF value which signifies
 * the LOA state.
 * 
 * @author mgere-oracle
 */
public class LOAAccountDisable extends TaskSupport {

	private static final Logger logger = Logger.getLogger(LOAAccountDisable.class.getName());

	@Override
	public void execute(HashMap arg0) throws Exception {
		logger.log(Level.INFO, "The scheduled task run has started.");

		if (arg0 == null) {
			// arg0 will never be null if a valid scheduled task definition file is used
			throw new SchedulerException("Scheduled task definition is incorrect. Aborting run.");
		}

		UserManager userManager = Platform.getService(UserManager.class);
		ProvisioningService provService = Platform.getService(ProvisioningService.class);

		final String LOA_DATE_FIELD_NAME = (String) arg0.get("LOA end date user attribute");
		logger.log(Level.FINE, "LOA_DATE_FIELD_NAME: {0}", LOA_DATE_FIELD_NAME);

		// construct a criteria for all active users in the system;
		// note that user access is disabled in this case, not the users themselves
		SearchCriteria userSearchCriteriaActive = new SearchCriteria(UserManagerConstants.AttributeName.STATUS.getId(),
				UserManagerConstants.AttributeValues.USER_STATUS_ACTIVE.getId(), SearchCriteria.Operator.EQUAL);
		Set<String> retAttrs = new HashSet<>();

		List<User> activeUserList = userManager.search(userSearchCriteriaActive, retAttrs, null);
		Date currentDate = Calendar.getInstance().getTime();
		logger.log(Level.FINE, "Current date: {0}", currentDate);

		for (User currentUser : activeUserList) {
			try {
				Date loaAccountDisableDate = (Date) currentUser.getAttribute(LOA_DATE_FIELD_NAME);

				if (loaAccountDisableDate != null) {
					logger.log(Level.INFO, "Processing user: {0}", currentUser.getLogin());
					logger.log(Level.FINE, "LOA account disable date: {0}", loaAccountDisableDate);

					String userStatus = currentUser.getStatus();
					logger.log(Level.FINE, "User status: {0}", userStatus);

					// calculate the difference in days between the LOA account disable date,
					// typically set in the future, and the current date
					Long dayDiff = TimeUnit.DAYS.convert(loaAccountDisableDate.getTime() - currentDate.getTime(),
							TimeUnit.MILLISECONDS);
					logger.log(Level.FINE, "Time diff: {0}", dayDiff);

					if (dayDiff <= 0
							&& userStatus.equals(UserManagerConstants.AttributeValues.USER_STATUS_ACTIVE.getId())) {
						logger.log(Level.INFO, "Parental leave date has been hit. Enabling user accounts...");

						SearchCriteria disableAccountSearch = new SearchCriteria(
								ProvisioningConstants.AccountSearchAttribute.ACCOUNT_STATUS.getId(),
								ProvisioningConstants.ObjectStatus.DISABLED.getId(), SearchCriteria.Operator.EQUAL);
						List<Account> disabledAccounts = provService.getAccountsProvisionedToUser(currentUser.getId(),
								disableAccountSearch, null);

						for (Account currentDisabledAccount : disabledAccounts) {
							try {
								logger.log(Level.INFO, "Enabling user account: {0}",
										currentDisabledAccount.getAccountDescriptiveField());
								provService.enable(Long.parseLong(currentDisabledAccount.getAccountID()));
								logger.log(Level.INFO, "Account enabled.");
							} catch (Exception e) {
								logger.log(Level.WARNING, "Enabling of account has failed: ", e);
							}
						}

						logger.log(Level.INFO, "Clearing LOA end date value...");
						User updatedUser = new User(currentUser.getId());
						updatedUser.setAttribute(LOA_DATE_FIELD_NAME, "");
						userManager.modify(updatedUser);
						logger.log(Level.INFO, "LOA end date cleared.");

					} else if (dayDiff > 0
							&& userStatus.equals(UserManagerConstants.AttributeValues.USER_STATUS_ACTIVE.getId())) {
						logger.log(Level.INFO, "A future LOA end date is set. Disabling user accounts...");

						// only list provisioned or enabled accounts, as those will be eligible for disabling
						SearchCriteria provisionedAccountSearch = new SearchCriteria(
								ProvisioningConstants.AccountSearchAttribute.ACCOUNT_STATUS.getId(),
								ProvisioningConstants.ObjectStatus.PROVISIONED.getId(), SearchCriteria.Operator.EQUAL);
						SearchCriteria enabledAccountSearch = new SearchCriteria(
								ProvisioningConstants.AccountSearchAttribute.ACCOUNT_STATUS.getId(),
								ProvisioningConstants.ObjectStatus.ENABLED.getId(), SearchCriteria.Operator.EQUAL);
						SearchCriteria activeAccountsSearch = new SearchCriteria(provisionedAccountSearch,
								enabledAccountSearch, SearchCriteria.Operator.OR);

						List<Account> activeAccounts = provService.getAccountsProvisionedToUser(currentUser.getId(),
								activeAccountsSearch, null);

						for (Account currentAccount : activeAccounts) {
							try {
								logger.log(Level.INFO, "Disabling user account: {0}",
										currentAccount.getAccountDescriptiveField());
								provService.disable(Long.parseLong(currentAccount.getAccountID()));
								logger.log(Level.INFO, "Account disabled.");
							} catch (Exception e) {
								logger.log(Level.WARNING, "Disabling of account has failed: ", e);
							}
						}
					}
				} else {
					logger.log(Level.FINE, "LOA end date not set. Skipping.");
				}
			} catch (Exception e) {
				logger.log(Level.WARNING, "User processing failed: ", e);
			}
		}

		logger.log(Level.INFO, "The scheduled task run has finished.");
	}

	@SuppressWarnings("rawtypes")
	@Override
	public HashMap getAttributes() {
		return new HashMap<>();
	}

	@Override
	public void setAttributes() {
	}
}
