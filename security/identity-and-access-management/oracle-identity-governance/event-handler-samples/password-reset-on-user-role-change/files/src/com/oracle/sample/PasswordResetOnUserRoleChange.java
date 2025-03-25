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

import java.io.Serializable;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

import oracle.iam.identity.usermgmt.api.UserManager;
import oracle.iam.identity.usermgmt.api.UserManagerConstants;
import oracle.iam.identity.usermgmt.vo.User;
import oracle.iam.platform.context.ContextAware;
import oracle.iam.platform.entitymgr.vo.SearchCriteria;
import oracle.iam.platform.Platform;
import oracle.iam.platform.kernel.OrchestrationEngine;
import oracle.iam.platform.kernel.spi.PreProcessHandler;
import oracle.iam.platform.kernel.vo.AbstractGenericOrchestration;
import oracle.iam.platform.kernel.vo.BulkEventResult;
import oracle.iam.platform.kernel.vo.BulkOrchestration;
import oracle.iam.platform.kernel.vo.EventResult;
import oracle.iam.platform.kernel.vo.Orchestration;

/**
 * 
 * Sample event handler implementation that triggers a user reset password
 * flow once a user's role changes. Note that in this context we are referring 
 * to a user role attribute, also known as "employee type", not to a change
 * in the membership status of a user to a particular OIG role.
 * 
 * @author mgere-oracle
 * 
 */
public class PasswordResetOnUserRoleChange implements PreProcessHandler {
	private static final Logger logger = Logger.getLogger(PasswordResetOnUserRoleChange.class.getName());

	private static final String ORCHESTRATION_CREATE_EVENT = "CREATE";
	private static final String ORCHESTRATION_MODIFY_EVENT = "MODIFY";

	@Override
	public EventResult execute(long arg0, long arg1, Orchestration arg2) {
		logger.log(Level.INFO, "Event handler execution has started.");

		EventResult eventResult = new EventResult();

		if (arg2 == null) {
			// arg2 will never be null if execute is called from an OIM event handler
			logger.log(Level.SEVERE, "Invalid orchestration payload.");
			eventResult.setFailureReason(new EventHandlerException("Invalid orchestration payload."));
		}

		else {
			try {
				HashMap<String, Serializable> parameters = arg2.getParameters();

				UserManager userManager = Platform.getService(UserManager.class);

				String operation = arg2.getOperation();
				logger.log(Level.INFO, "Orchestration event: {0}", operation);

				// should only run on MODIFY orchestration events, as per provided metadata
				if (operation.equals(ORCHESTRATION_MODIFY_EVENT)) {
					String userKey = getUserKey(arg0, arg2);
					logger.log(Level.FINE, "User Key: {0}", userKey);

					String userEmpType = getParamaterValue(parameters,
							UserManagerConstants.AttributeName.EMPTYPE.getId());
					logger.log(Level.FINE, "User EmpType: {0}", userEmpType);

					Set<String> retAttrs = new HashSet<>();
					SearchCriteria searchCriteria = new SearchCriteria(
							UserManagerConstants.AttributeName.USER_KEY.getId(), userKey,
							SearchCriteria.Operator.EQUAL);

					User modifiedUser = userManager.search(searchCriteria, retAttrs, null).get(0);

					// should only trigger when the role/empType changes
					if (userEmpType != null
							&& parameters.containsKey(UserManagerConstants.AttributeName.EMPTYPE.getId())) {
						logger.log(Level.INFO, "Resetting user password for: {0}", modifiedUser.getLogin());
						userManager.resetPassword(userKey, false);
					}
				} else {
					logger.log(Level.SEVERE, "Invalid event type.");
					eventResult.setFailureReason(new EventHandlerException("Invalid event type."));
				}
			} catch (Exception e) {
				logger.log(Level.SEVERE, "User password reset has failed with: ", e);
				eventResult.setFailureReason(e);
			}
		}

		logger.log(Level.INFO, "Event handler execution has stopped");
		return eventResult;
	}

	/**
	 * Retrieve ContextAware values of parameters from an event handler
	 * orchestration event, based on a desired key.
	 * 
	 * @param parameters
	 * @param key
	 * @return
	 */
	private String getParamaterValue(HashMap<String, Serializable> parameters, String key) {
		if (parameters.containsKey(key)) {
			return (parameters.get(key) instanceof ContextAware)
					? (String) ((ContextAware) parameters.get(key)).getObjectValue()
					: (String) parameters.get(key);
		} else {
			return null;
		}
	}

	/**
	 * Return the affected user key from an orchestration event.
	 * 
	 * @param processID
	 * @param orchestration
	 * @return
	 */
	private String getUserKey(long processID, Orchestration orchestration) {
		String userKey;

		if (!orchestration.getOperation().equals(ORCHESTRATION_CREATE_EVENT)) {
			userKey = orchestration.getTarget().getEntityId();
		} else {
			OrchestrationEngine orchEngine = Platform.getService(OrchestrationEngine.class);
			userKey = (String) orchEngine.getActionResult(processID);
		}

		return userKey;
	}

	@Override
	public void initialize(HashMap<String, String> arg0) {
	}

	@Override
	public void compensate(long arg0, long arg1, AbstractGenericOrchestration arg2) {
	}

	@Override
	public boolean cancel(long arg0, long arg1, AbstractGenericOrchestration arg2) {
		return false;
	}

	@Override
	public BulkEventResult execute(long arg0, long arg1, BulkOrchestration arg2) {
		BulkEventResult bulkEventResult = new BulkEventResult();

		logger.log(Level.WARNING, "The event handler does not reset passwords for bulk events.");

		return bulkEventResult;
	}
}