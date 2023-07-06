/*******************************************************************************
 * Copyright (c) 2023 Oracle and/or its affiliates. All rights reserved. DO NOT
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
import oracle.iam.scheduler.exception.SchedulerException;
import oracle.iam.scheduler.vo.TaskSupport;

/**
 * Sample scheduled task implementation that disables a user until a future
 * enablement date is hit. The scheduled task will also clear the existing
 * enablement date after enabling a user.
 * 
 * @author mgere-oracle
 */
public class TemporaryUserDisable extends TaskSupport {

	private static final Logger logger = Logger.getLogger(TemporaryUserDisable.class.getName());

	@Override
	public void execute(HashMap arg0) throws Exception {
		logger.log(Level.INFO, "The scheduled task run has started.");
		
		if (arg0 == null) {
			// arg0 will never be null if a valid scheduled task definition file is used
			throw new SchedulerException("Scheduled task definition is incorrect. Aborting run.");
		}

		UserManager userManager = Platform.getService(UserManager.class);

		// the arg0 HashMap key needs to be identical to the field name
		// as it was specified in the scheduled task definition (xml file)
		final String DATE_FIELD_NAME = (String) arg0.get("Temporary disable date user attribute");
		logger.log(Level.FINE, "DATE_FIELD_NAME: {0}", DATE_FIELD_NAME);

		// construct a criteria for all active and disabled users in the system
		SearchCriteria userSearchCriteriaActive = new SearchCriteria(UserManagerConstants.AttributeName.STATUS.getId(),
				UserManagerConstants.AttributeValues.USER_STATUS_ACTIVE.getId(), SearchCriteria.Operator.EQUAL);
		SearchCriteria userSearchCriteriaDisabled = new SearchCriteria(
				UserManagerConstants.AttributeName.STATUS.getId(),
				UserManagerConstants.AttributeValues.USER_STATUS_DISABLED.getId(), SearchCriteria.Operator.EQUAL);
		SearchCriteria userSearchCriteria = new SearchCriteria(userSearchCriteriaActive, userSearchCriteriaDisabled,
				SearchCriteria.Operator.OR);
		Set<String> retAttrs = new HashSet<>();

		List<User> returnedUserList = userManager.search(userSearchCriteria, retAttrs, null);
		Date currentDate = Calendar.getInstance().getTime();
		logger.log(Level.FINE, "Current date: {0}", currentDate);

		for (User currentUser : returnedUserList) {
			try {
				String userLogin = currentUser.getLogin();
				Date temporaryDisableDate = (Date) currentUser.getAttribute(DATE_FIELD_NAME);

				if (temporaryDisableDate != null) {
					logger.log(Level.INFO, "Processing user: {0}", userLogin);
					logger.log(Level.FINE, "Temporary disable date: {0}", temporaryDisableDate);

					String userStatus = currentUser.getStatus();
					logger.log(Level.FINE, "User status: {0}", userStatus);

					// calculate the difference in days between the temporary disable date,
					// typically set in the future, and the current date
					Long dayDiff = TimeUnit.DAYS.convert(temporaryDisableDate.getTime() - currentDate.getTime(),
							TimeUnit.MILLISECONDS);
					logger.log(Level.FINE, "Time diff: {0}", dayDiff);

					// the temporary disable date is in the future and the user is active;
					// action -> disable the user
					if (dayDiff > 0
							&& userStatus.equals(UserManagerConstants.AttributeValues.USER_STATUS_ACTIVE.getId())) {
						logger.log(Level.INFO, "User has a valid future temporary disable date set. Disabling...");
						userManager.disable(userLogin, true);
						logger.log(Level.INFO, "User disabled.");
					}

					// the temporary disable date has been reached and the user is disabled;
					// action -> enable the user and clear the temporary disabled date
					else if (dayDiff <= 0
							&& userStatus.equals(UserManagerConstants.AttributeValues.USER_STATUS_DISABLED.getId())) {
						logger.log(Level.INFO, "Disable until date has been hit. Enabling user...");
						userManager.enable(userLogin, true);
						logger.log(Level.INFO, "User enabled.");

						logger.log(Level.FINE, "Clearing temporary disable date value...");

						User updatedUser = new User(currentUser.getId());
						updatedUser.setAttribute(DATE_FIELD_NAME, "");
						userManager.modify(updatedUser);

						logger.log(Level.FINE, "Temporary disable date cleared.");
					}

				} else {
					logger.log(Level.FINE, "Temporary disable date not set. Skipping.");
				}
			} catch (Exception e) {
				logger.log(Level.WARNING, "User processing failed: ", e);
			}
		}

		logger.log(Level.INFO, "The scheduled task run has finished.");
	}

	@Override
	public HashMap getAttributes() {
		return new HashMap<>();
	}

	@Override
	public void setAttributes() {
	}
}
